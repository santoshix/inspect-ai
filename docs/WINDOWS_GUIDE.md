# Windows guide — from ZIP to your first prediction

## 1. Extract it

Right-click the downloaded ZIP → **Extract All**. Open the extracted folder, then open `inspect-ai`. You should see `README.md`, `setup_windows.bat`, `START_INSPECTAI.bat`, `models`, and `samples`.

Use a short folder such as `C:\Projects\InspectAI`. Avoid running from inside a ZIP. A regular local folder outside OneDrive helps avoid file locks and slow syncing.

## 2. Check Python

Open VS Code → File → Open Folder → select `inspect-ai`. Open Terminal → New Terminal. Run:

```powershell
py -0p
```

If Python 3.12 is listed, continue. If not, install Python 3.12, 64-bit, from python.org and include the Python Launcher. Close and reopen VS Code after installation. This project uses its own environment, separate from FraudShield.

## 3. Install packages once

In File Explorer, double-click `setup_windows.bat`. Wait until it says setup complete. The first install downloads PyTorch and other packages and may take several minutes. Do not close it halfway through.

Alternatively paste each command from README's manual PowerShell setup one at a time. Do not paste the `PS C:\...>` prompt.

## 4. Start

Double-click `START_INSPECTAI.bat`. Wait for `Application startup complete`. Open Chrome yourself and type:

**http://127.0.0.1:8000**

Do not open `index.html` directly; the page needs its API server.

## 5. Inspect

Click a sample thumbnail below the upload box. Try `defect_01.png`, then `clean_01.png`. Coral boxes show detected regions. Check the confidence, inference time and new history row. Download an annotated image or export CSV.

Next click “Choose or drop an image,” select a file from `samples`, and click “Run inspection.” You can try your own photo, but the bundled model is only validated on synthetic textures; an unexpected result is not proof your real product is good or bad.

## 6. Run the tests

Open a second VS Code terminal in `inspect-ai`:

```powershell
.\.venv-inspect\Scripts\python.exe -m pytest -q
```

## 7. Stop and reopen

In the server terminal press Ctrl+C. Next time, only run `START_INSPECTAI.bat` again. You do not need to reinstall or retrain. History stays in `runtime/inspections.db`.

## Troubleshooting

| Message or symptom | Fix |
|---|---|
| `py is not recognized` | Install Python with the Python Launcher, reopen VS Code. |
| No suitable Python runtime | Install Python 3.12 specifically. |
| `No module named ...` | Run setup again; use `.venv-inspect\Scripts\python.exe`, not a different project's Python. |
| Port 8000 already in use | Stop FraudShield's server with Ctrl+C, or run the command below on port 8001. |
| Browser cannot connect | Keep the terminal open and wait for startup; check for terminal errors. |
| Missing model | Ensure you extracted the whole ZIP, including `models/defect_yolo.pt`. |
| Upload rejected | Use an intact PNG/JPEG, under 8 MB and 16 megapixels. |
| No model package wheel available | Verify 64-bit Python 3.12. Share the exact pip error if it still fails. |
| Powershell script execution blocked | Use the direct Python commands; no environment activation is needed. |

Alternative port:

```powershell
.\.venv-inspect\Scripts\python.exe -m uvicorn inspection.api:app --host 127.0.0.1 --port 8001
```

Then visit **http://127.0.0.1:8001**. The frontend uses relative API URLs, so no code change is needed.
