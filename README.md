# Inspect-AI — Computer Vision Defect Inspection

**A working local visual-inspection application** built with **YOLOv8n, PyTorch, OpenCV, FastAPI, SQLite, and Docker**. Upload a surface image, detect and highlight suspected defects, review inspection history, and export inspection results.

> **Educational research demo:** The trained detector learns from **synthetic surface textures**, not real factory photographs. Its results do not establish production inspection accuracy or product safety. It detects one label, `surface_defect`, rather than separate scratch, stain, or pit categories.

## Model performance — held-out synthetic test set

| Metric | Result |
|---|---:|
| Detection mAP@50 | **95.56%** |
| Detection mAP@50:95 | **82.15%** |
| Detection precision (Ultralytics best-F1 point) | **98.17%** |
| Detection recall (Ultralytics best-F1 point) | **90.40%** |
| Warm CPU inference p95 | **10.93 ms** |

The evaluation uses **120 test images** from a synthetic dataset with **480 train / 120 validation / 120 test** images. The 10.93 ms measurement covers warm `model.predict` calls only—it **excludes** HTTP, decoding, annotation rendering, and database work. The reported detection precision and recall use Ultralytics' best-F1 operating point; the dashboard's default threshold is **0.35**. The test results are from the **same synthetic image generator family** as training, so they cannot be generalized to real industrial defects.

Read the source measurements in [`reports/evaluation.json`](reports/evaluation.json) and methodology in [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

## What you can do

- **Real model inference:** Run the shipped YOLOv8n checkpoint locally on CPU, with bounding boxes and confidence scores.
- **Web-based inspection:** Upload PNG/JPEG images or use included samples; adjust the confidence threshold and download annotated results.
- **History and exports:** Store inspection metadata in SQLite, view results and counts, and export CSV or JSON.
- **Backend API:** Access FastAPI interactive documentation, including image inspection and saved inspection summaries.
- **Batch workflow:** Run the inspector over a folder from the command line.
- **Reproducible ML:** Generate labeled synthetic data, retrain the detector, and rerun an isolated test evaluation.
- **Tests and packaging:** Automated Python tests, GitHub Actions, a Dockerfile, Compose, and Windows startup scripts.

## How it works

```text
Browser image upload / sample
          ↓
FastAPI (validate image and orientation)
          ↓
Pillow / OpenCV image preparation
          ↓
PyTorch + YOLOv8n defect detection
          ↓
Bounding boxes + annotated image response
          ↓
SQLite inspection metadata + browser history
```

The app is a single-process, local demo. Upload and annotated image bytes are returned to the browser and **not persisted by the server**; only inspection metadata is stored. Inference uses a shared lock around the Ultralytics predictor.

## Quick start — Windows

The trained checkpoint and example images are already included. **No GPU, cloud account, model API key, or training step is required.** Initial dependency installation requires an internet connection.

1. Install **64-bit Python 3.12** with the Python Launcher.
2. Clone this repository or download and extract its ZIP to a regular folder.
3. In the project folder, double-click **`setup_windows.bat`** to create the isolated environment and install dependencies.
4. Double-click **`START_INSPECTAI.bat`**.
5. Open **http://127.0.0.1:8000** in your browser.
6. Try a bundled `defect_01.png` or `clean_01.png` sample, then upload another PNG/JPEG and click **Run inspection**.

For a Git-based checkout:

```powershell
git clone https://github.com/santoshix/inspect-ai.git
cd inspect-ai
```

Keep the server terminal open while using the app. Stop it with **Ctrl+C**. See [Windows setup and troubleshooting](docs/WINDOWS_GUIDE.md) for step-by-step commands and common problems. Windows launch scripts are supplied, but the original delivery verification was done on Linux rather than a Windows host.

### Manual Windows installation (VS Code → Terminal)

```powershell
py -3.12 -m venv .venv-inspect
.\.venv-inspect\Scripts\python.exe -m pip install --upgrade pip
.\.venv-inspect\Scripts\python.exe -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
.\.venv-inspect\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-inspect\Scripts\python.exe -m uvicorn inspection.api:app --host 127.0.0.1 --port 8000
```

**API docs:** http://127.0.0.1:8000/docs. On Linux, create `.venv-inspect` with Python 3.12, install the same dependencies using `.venv-inspect/bin/python`, and run `bash start.sh`. macOS is not a validated target.

## Run automated tests

With dependencies installed:

```powershell
.\.venv-inspect\Scripts\python.exe -m pytest -q
```

The repository's [GitHub Actions workflow](../../actions) runs tests on pushes and pull requests. The latest public GitHub run should be checked separately; the original [delivery verification notes](reports/verification.txt) describe tests executed at packaging time and their limits. **CI tests do not establish real-world visual inspection performance.**

## Reproduce training and evaluation

The shipped checkpoint is ready to use. To regenerate/retrain it, stop the server and **back up `models/defect_yolo.pt`** first (the training process replaces it).

```powershell
.\.venv-inspect\Scripts\python.exe -m scripts.generate_data
.\.venv-inspect\Scripts\python.exe -m scripts.train --epochs 40
.\.venv-inspect\Scripts\python.exe -m scripts.evaluate
```

Training initializes the `yolov8n.yaml` model architecture from scratch without downloading a pretrained COCO checkpoint. Validation selects the saved checkpoint; held-out test data is used only for evaluation. Retraining metrics may vary across CPUs and library versions. The bundled model uses a **128-pixel model input**, which limits sensitivity to very small defects.

To transition to actual industrial images, follow the [real-data validation guide](docs/REAL_DATA_GUIDE.md). A real-data evaluation would require labeled real product photos, product/batch-aware splits, threshold selection on validation data, and an independent test set.

## API endpoints

| Endpoint | Function |
|---|---|
| `GET /health` | Application/model health |
| `POST /api/inspect` | Inspect a user-uploaded image |
| `POST /api/inspect-sample/{name}` | Inspect a bundled sample |
| `GET /api/history` | Recent inspection metadata |
| `GET /api/summary` | Inspection counts and timing |
| `GET /api/model-report` | Stored synthetic-data evaluation |
| `GET /api/export.csv` | Download recent inspection history |

For example, from the project directory with the server running:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/inspect" -F "file=@samples/defect_01.png" -F "threshold=0.35"
```

The model's confidence scores are **not calibrated probabilities**, nor proof a surface is safe. Image coordinates correspond to the returned displayed image after orientation/resizing.

## Optional Docker

```bash
docker compose up --build
```

Visit http://127.0.0.1:8000. The Compose port binds to localhost and a named volume preserves SQLite history. `docker compose down` stops the app; `docker compose down -v` **deletes** the persisted inspection history. Docker setup is provided, but the original delivery verification did **not** include a successful Docker runtime test.

## Repository map

```text
inspection/           FastAPI, YOLO inference, validation, SQLite
web/                  HTML/CSS/JavaScript inspection dashboard
models/               Included trained checkpoint and metadata
samples/              Example images
data/                 Synthetic train/validation/test images and YOLO labels
scripts/              Generate, train, evaluate, and batch inspect
reports/              Measured model results and verification notes
docs/                 Windows guide, model card, real-data guide
tests/                Model, API, upload and persistence checks
setup_windows.bat     Windows dependency installation
START_INSPECTAI.bat   Windows server launcher
Dockerfile            Container build
compose.yaml          Local Docker deployment
```

## Interview-ready description

> Built Inspect-AI, a local computer vision inspection application with YOLOv8n, PyTorch, OpenCV, FastAPI, and SQLite. Trained a one-class object detector on 720 synthetic surface images, achieving 95.56% mAP@50 and 82.15% mAP@50:95 on a held-out synthetic test split. Implemented image upload, annotated predictions, inspection history, export tools, Docker packaging, and automated tests.

## Limitations and responsible use

This is a **synthetic-data research demo**, not a validated quality-control system. Before real production use it would require a representative real-world labeled dataset, material- and product-specific testing, failure analysis, well-calibrated review thresholds, authentication, upload limits at the proxy, TLS, observability, and operational safeguards. A missing detection is **not** proof that a product is defect-free.

**Licensing:** Ultralytics YOLO has its own AGPL-3.0 licensing obligations. Read [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), [`LICENSE-ULTRALYTICS`](LICENSE-ULTRALYTICS), and the [Ultralytics licensing page](https://www.ultralytics.com/license). Do not assume a permissive license from the repository being public.
