#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
exec .venv-inspect/bin/python -m uvicorn inspection.api:app --host 127.0.0.1 --port 8000
