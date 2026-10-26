from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timezone
import os, json, uuid

BASE = Path(__file__).resolve().parent
UPLOAD_DIR = BASE / 'uploads'
OUTPUT_DIR = BASE / 'outputs'
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CONFIG_PATH = BASE / 'config.json'
EVENTS_PATH = BASE / 'events.jsonl'
ALLOWED = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.jpg', '.jpeg', '.png'}
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = str(UPLOAD_DIR)

DEFAULT_CONFIG = {
    'max_passengers': 40,
    'alert_at_limit': True,
    'authority_webhook_url': '',
    'authority_api_token': '',
    'iot_mode': 'mock',
    'iot_endpoint': '',
    'cctv_source': '',
    'bus_id': 'TN-TRANSMIT-DEMO-01'
}

def read_config():
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            return {**DEFAULT_CONFIG, **saved}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def log_event(event_type, message, level='info', details=None):
    event = {
        'id': str(uuid.uuid4())[:8],
        'timestamp': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),
        'type': event_type, 'message': message, 'level': level,
        'details': details or {}
    }
    with EVENTS_PATH.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def get_events(limit=50):
    if not EVENTS_PATH.exists():
        return []
    rows = []
    for line in EVENTS_PATH.read_text(encoding='utf-8').splitlines()[-limit:]:
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    return list(reversed(rows))

@app.get('/')
def index():
    return render_template('index.html', config=read_config(), events=get_events())

@app.get('/api/status')
def status():
    cfg = read_config()
    return jsonify({
        'ok': True, 'bus_id': cfg['bus_id'], 'max_passengers': cfg['max_passengers'],
        'cctv_configured': bool(cfg.get('cctv_source')),
        'authority_configured': bool(cfg.get('authority_webhook_url')),
        'iot_mode': cfg.get('iot_mode', 'mock'),
        'events': get_events(10)
    })

@app.post('/api/settings')
def settings():
    data = request.get_json(silent=True) or {}
    cfg = read_config()
    try:
        limit = int(data.get('max_passengers', cfg['max_passengers']))
        if not 1 <= limit <= 1000:
            return jsonify(ok=False, error='Passenger limit must be between 1 and 1000.'), 400
    except (TypeError, ValueError):
        return jsonify(ok=False, error='Passenger limit must be a whole number.'), 400
    cfg['max_passengers'] = limit
    cfg['alert_at_limit'] = bool(data.get('alert_at_limit', True))
    cfg['bus_id'] = str(data.get('bus_id', cfg['bus_id']))[:80]
    # Keep secrets/endpoints server-side; update only when explicitly submitted.
    for key in ('authority_webhook_url', 'authority_api_token', 'iot_mode', 'iot_endpoint', 'cctv_source'):
        if key in data:
            cfg[key] = str(data[key]).strip()
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding='utf-8')
    log_event('settings', f"Settings updated. Passenger limit: {limit}")
    return jsonify(ok=True, config={k:v for k,v in cfg.items() if 'token' not in k})

@app.post('/api/upload')
def upload():
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify(ok=False, error='Choose a video or image first.'), 400
    safe_name = secure_filename(file.filename)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED:
        return jsonify(ok=False, error='Supported formats: MP4, AVI, MOV, MKV, WEBM, JPG, JPEG, PNG.'), 400
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}_{safe_name}"
    target = UPLOAD_DIR / unique_name
    file.save(target)
    is_image = suffix in {'.jpg', '.jpeg', '.png'}
    event = log_event('upload', f"Uploaded {'image' if is_image else 'video'}: {safe_name}", details={'stored_as': unique_name})
    # Upload storage is implemented; model inference is deliberately reported as pending
    # until the user's model weights, tracker and calibrated entry/exit zones are connected.
    return jsonify(ok=True, filename=unique_name, original_name=safe_name,
                   media_type='image' if is_image else 'video',
                   message='File uploaded. Connect the trained detector/tracker and define entry/exit zones to run real analysis.',
                   event=event), 201

@app.get('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)

@app.post('/api/alert')
def alert():
    data = request.get_json(silent=True) or {}
    kind = str(data.get('type', 'manual'))[:40]
    message = str(data.get('message', 'Manual test alert'))[:500]
    level = str(data.get('level', 'warning'))[:20]
    event = log_event(kind, message, level, data.get('details', {}))
    # This logs the event locally. A real authority webhook is added only after its
    # exact API contract/authentication is provided and tested.
    return jsonify(ok=True, event=event, authority_forwarded=False,
                   note='Saved locally. Configure and implement your authority website API before claiming delivery.'), 201

@app.post('/api/iot/test')
def iot_test():
    cfg = read_config()
    # Safe by default: no live relay/door command is sent from this demo.
    event = log_event('iot_test', 'IoT integration test requested; no physical door command sent.', 'info',
                      {'mode': cfg.get('iot_mode', 'mock')})
    return jsonify(ok=True, mode=cfg.get('iot_mode', 'mock'), event=event,
                   message='Mock test only. No door actuator was operated. Use the device maker’s documented interface and an independent safety controller for real hardware.')

@app.get('/api/events')
def events():
    return jsonify(events=get_events(100))

@app.get('/health')
def health():
    return jsonify(status='ok', service='TN Transmit Smart Crowd AI starter')

if __name__ == '__main__':
    print('TN Transmit Smart Crowd AI starter: http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=True)
