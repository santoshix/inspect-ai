# InspectAI — Visual Defect Detection & AI Inspection System

A complete local computer-vision portfolio project: upload an image, detect surface defects with a trained YOLOv8n model, inspect bounding boxes, and keep an auditable inspection history.

**Ready to run:** the trained checkpoint and example images are included. No AWS, GPU, credentials, or external inference API required. First-time dependency installation needs internet.

**Scope:** an educational system trained and evaluated on original synthetic textures. It is not a validated production quality-control system. The model predicts one class, `surface_defect`; it does not distinguish scratch, pit, and stain subtypes or certify that a product is safe. Real photographs need real labeled training data and independent validation.

## Start on Windows

1. Extract the entire ZIP to a normal folder such as `C:\Projects\InspectAI`.
2. Install 64-bit **Python 3.12** with the Python Launcher if you do not have it.
3. Inside `inspect-ai`, double-click `setup_windows.bat` and wait for success.
4. Double-click `START_INSPECTAI.bat`.
5. After the terminal says startup is complete, open **http://127.0.0.1:8000** in Chrome.
6. Click a sample thumbnail or upload a PNG/JPEG, then choose **Run inspection**.

Keep the terminal open while using the dashboard. Press Ctrl+C to stop.

For copy-and-paste commands and troubleshooting, see [the Windows guide](docs/WINDOWS_GUIDE.md).

## Included capabilities

- Actual PyTorch-backed YOLOv8n object detection, trained from scratch on the included data.
- Bounding boxes, confidence threshold adjustment, image-level decisions and model timing.
- OpenCV image processing and annotated image export; EXIF rotation handled before inference.
- FastAPI JSON API with Swagger documentation at `/docs`.
- Responsive browser dashboard; no Node.js build or separate frontend server needed.
- SQLite inspection history, summary counts, and CSV/JSON export.
- Batch folder inspection from the command line.
- Deterministic synthetic-data generator; train/validation/test directories and box labels.
- Retraining script, test evaluation, measured results, and checkpoint hash.
- Automated tests covering real model inference, upload validation, persistence and exports.
- Dockerfile, Compose configuration, local startup scripts and GitHub Actions test workflow.

## Architecture

The browser sends an image to FastAPI. Pillow validates it and applies EXIF orientation, then OpenCV converts its pixels. A shared YOLO detector predicts bounding boxes; the app draws annotations and saves metadata to SQLite. The browser displays the image and refreshes history. Raw uploads and annotated image bytes are **not persisted** by the server. You can download the result yourself.

Inference requests share a lock because the Ultralytics predictor is mutable. A thread pool keeps model work off the asynchronous request loop. This is a single-process, local demo; it is not a distributed inference queue.

## Folder map

```text
inspection/          API, model inference, image decoding, SQLite storage
web/                 Browser dashboard: HTML, CSS and JavaScript
models/              Trained YOLO checkpoint + metadata
samples/             Independent synthetic examples for the dashboard
data/                480 training / 120 validation / 120 test images + labels
scripts/             Generate data, train, evaluate, batch inference
reports/             Actual evaluation, training history and verification results
tests/               Automated model/API/storage tests
docs/                Windows guide, model card, real-data guide, demo script
runtime/             Created at runtime: local database and resolved data paths
```

## Manual setup (PowerShell)

Open the `inspect-ai` folder in VS Code, then Terminal → New Terminal:

```powershell
py -3.12 -m venv .venv-inspect
.\.venv-inspect\Scripts\python.exe -m pip install --upgrade pip
.\.venv-inspect\Scripts\python.exe -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
.\.venv-inspect\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-inspect\Scripts\python.exe -m uvicorn inspection.api:app --host 127.0.0.1 --port 8000
```

Commands use the environment's Python directly; PowerShell activation is unnecessary.

## Linux setup

```bash
python3.12 -m venv .venv-inspect
.venv-inspect/bin/python -m pip install --upgrade pip
.venv-inspect/bin/python -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
.venv-inspect/bin/python -m pip install -r requirements-dev.txt
bash start.sh
```

Validated on Linux CPU/Python 3.12. Windows launch scripts are supplied but have not been executed on a Windows machine here. CPU wheel availability depends on OS and architecture; this setup targets 64-bit Windows/Linux. macOS is not a validated target.

## Run tests

In a second terminal, with the project folder open:

```powershell
.\.venv-inspect\Scripts\python.exe -m pytest -q
```

Tests use a temporary database, not your dashboard history. See `reports/verification.txt` for the delivery-time results.

## Training and evaluation

You do not need to train before using the included demo. To reproduce it, stop the server first:

```powershell
.\.venv-inspect\Scripts\python.exe -m scripts.generate_data
.\.venv-inspect\Scripts\python.exe -m scripts.train --epochs 40
.\.venv-inspect\Scripts\python.exe -m scripts.evaluate
```

The generator replaces generated split PNG/TXT files. Training uses `yolov8n.yaml` architecture initialization, so it does not require pretrained COCO weights. Validation selects the checkpoint; the test split is used only for evaluation. Retraining replaces `models/defect_yolo.pt`; back up that file to keep the shipped model. Hardware/library differences can change results even with fixed seeds.

The default inference threshold is **0.35**, chosen before test evaluation. Reported image metrics use this threshold; Ultralytics detection precision/recall are reported at its best-F1 point, which is a different operating point. mAP integrates over confidence thresholds.

`reports/evaluation.json` contains actual measured metrics and machine-dependent latency. Do not describe these as real-world manufacturing accuracy.

## Batch inference

```powershell
.\.venv-inspect\Scripts\python.exe -m scripts.batch_inspect samples --output runtime/batch
```

Produces annotated PNGs and `results.json`. This CLI does not add records to the web dashboard database.

## API examples

With the server running, open http://127.0.0.1:8000/docs → `POST /api/inspect` → Try it out → choose a file → Execute.

Or in PowerShell:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/inspect" -F "file=@samples/defect_01.png" -F "threshold=0.35"
```

| Endpoint | Purpose |
|---|---|
| `GET /health` | Confirms model startup |
| `POST /api/inspect` | Multipart image + threshold |
| `POST /api/inspect-sample/{name}` | Inspect a bundled sample |
| `GET /api/history` | Latest inspection metadata |
| `GET /api/summary` | Counts and average model inference time |
| `GET /api/model-report` | Frozen synthetic test results |
| `GET /api/export.csv` | Latest 10,000 records as CSV |

Bounding boxes are `[x1,y1,x2,y2]` in the returned displayed image's coordinate space, after orientation and optional resizing. The image is further letterboxed to a 128-pixel model input internally. Scores are not calibrated probabilities.

## Docker (optional)

Install and start Docker Desktop, then from the project directory:

```powershell
docker compose up --build
```

Open http://127.0.0.1:8000. Stop with Ctrl+C, then `docker compose down`. History is preserved in a named Docker volume. `docker compose down -v` deletes that history. The Compose port is bound to localhost. Docker configuration is included; see the verification report for whether it was executed in the build environment.

## Publish your source to GitHub

Create an empty repository named `inspectai` in your own GitHub account. Do not initialize it with a README if you follow these commands. Open the `inspect-ai` folder in VS Code:

```powershell
git init
git add .
git commit -m "Build InspectAI visual defect inspection system"
git branch -M main
git remote add origin https://github.com/santoshshah2003/inspectai.git
git push -u origin main
```

That URL is the suggested destination, not a repository created by this package. Use your actual repository URL if different. The model and data are small enough for a demo repository. Virtual environments, runtime history and training run directories are ignored.

## Responsible project claims

Once you have run and understood the project, a factual description is:

“Built a local visual inspection application using PyTorch-backed YOLOv8n, OpenCV and FastAPI. Trained and evaluated a one-class defect detector on synthetic surface images, served annotated predictions through a browser dashboard, and added persistent inspection history, exports and automated tests.”

Add measured metrics only with the synthetic-test qualification. Do not claim AWS deployment, real factory validation, independent authorship without assistance, or production readiness. Be ready to explain the training split, IoU, confidence threshold, false negatives, and API flow.

## Production work still required

Real defect data, per-product validation, calibrated operating thresholds, monitoring for drift, authentication, transport security, reverse-proxy request limits, load tests, backup policy and an operational review are required before external or industrial use. The app intentionally defaults to local-only access. Upload validation happens after multipart parsing; use an upstream body limit before exposing it publicly. Only load model checkpoints from trusted sources.

## Sources and dependencies

- [Ultralytics training](https://docs.ultralytics.com/modes/train/)
- [Ultralytics Python usage](https://docs.ultralytics.com/usage/python/)
- [FastAPI file uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [PyTorch installation](https://pytorch.org/get-started/locally/)

See `THIRD_PARTY_NOTICES.md` for dependency and model licensing notes.
