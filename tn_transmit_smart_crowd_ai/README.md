# TN Transmit Smart Crowd AI — starter website

A Flask dashboard prototype for the TN Transmit Smart Crowd AI project. It includes media upload and preview, configurable passenger threshold, bilingual browser speech test alerts, event history, and configuration placeholders for CCTV, authority webhooks, and IoT.

## Run on Windows PowerShell

1. Install Python 3.11 or 3.12 (recommended for the later OpenCV/YOLO integration).
2. Open PowerShell in this folder.
3. Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run commands directly using `\.venv\Scripts\python.exe` or use Command Prompt activation `\.venv\Scripts\activate.bat`.

4. Install dependencies and run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python app.py
```

5. Open `http://127.0.0.1:5000` in your browser.

## What is implemented

- Responsive dashboard UI.
- Upload and preview common video/image files.
- Save configuration for passenger limit, vehicle ID, CCTV source, IoT mode/endpoint, and authority endpoint.
- Local event log and API endpoints: `/api/status`, `/api/settings`, `/api/upload`, `/api/alert`, `/api/iot/test`, `/api/events`, `/health`.
- Browser-based English and Tamil announcement test buttons.
- IoT test is mock-only; it does not issue a door movement command.

## Not yet implemented — must be connected and tested

1. YOLO/OpenCV inference on uploaded media.
2. Person tracking with unique track IDs and calibrated entry/exit lines.
3. Reliable occupancy calculation (entry/exit counts alone need a known initial occupancy and reset/reconciliation logic).
4. Door-step obstruction sensor and hardware feedback.
5. Delivery to the authority website. A URL alone is not enough: obtain its expected API route, JSON schema, authentication, TLS/network access, and acknowledgement response.
6. Real CCTV stream ingestion. Browser support varies; RTSP normally requires backend access and may need a stream bridge.
7. Real IoT protocol adapter. Obtain the device make/model, protocol, wiring/interface and documented API. Do not connect a relay or motor to an unverified endpoint.

## Safety notes

- This is a prototype, not a certified passenger-safety system.
- The independent physical door controller must prevent closing while an obstruction is present. AI/video should not be the sole door safety interlock.
- Fail safe on sensor uncertainty, controller/network failure, or loss of power; retain manual/emergency override.
- Do not expose this Flask development server publicly. Use authenticated production hosting, HTTPS, access controls, rate limiting, and secure secret storage before any external integration.
- Configure the passenger threshold according to the specific vehicle's approved capacity and applicable transport rules.
- Browser speech depends on installed voices, browser permissions and speaker hardware. For an actual bus PA, use an approved audio/controller interface.

## Recommended integration sequence

1. Confirm the detector and tracker, then process saved video offline.
2. Calibrate entry/exit lines on sample clips; verify counts manually across several lighting and crowd conditions.
3. Add a doorway ROI and obstruction dwell-time logic, but use the physical safety sensor as the authoritative interlock.
4. Implement and test authority webhook delivery with retry, unique event IDs, acknowledgements and delivery status.
5. Implement the device-specific IoT adapter in a bench test, initially with a dummy load, and only after the controller's safety requirements are understood.
6. Add live CCTV after offline video processing is reliable.
