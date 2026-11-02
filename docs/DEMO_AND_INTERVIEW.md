# Two-minute project walkthrough

1. Open the dashboard. Explain: “This is a local inspection application trained on synthetic surface defects.”
2. Select a defective sample. Point to the detected region and its confidence.
3. Select a clean sample. Explain that “no defect detected” is a prediction, not a guarantee.
4. Upload a sample manually and move the confidence slider. Explain the false-positive/false-negative tradeoff.
5. Show inspection history and export CSV. Open `/docs` to show the same functionality as an API.
6. Show the model evaluation panel and explain the synthetic test set and its limitations.
7. Show `python -m pytest -q` passing in your terminal.

## Concepts to understand before an interview

- **YOLO:** predicts object bounding boxes and class scores in an image. Here the only class is surface defect.
- **PyTorch:** executes the neural network and supplies training/autograd infrastructure.
- **OpenCV:** handles color conversion and bounding-box rendering in the service.
- **IoU:** intersection area divided by union area for two boxes; used to judge localization and suppress duplicate detections.
- **Confidence threshold:** minimum score for keeping a detection. Raising it usually reduces both false alarms and recall.
- **Precision:** among predicted positives, the proportion that are correct.
- **Recall:** among actual positives, the proportion found.
- **mAP:** summarizes detection quality across confidence thresholds; mAP@50 and mAP@50:95 use different IoU requirements.
- **Leakage:** training and testing on related copies can inflate results; keep physical items and batches separate.
- **FastAPI:** exposes the trained detector through an HTTP endpoint.
- **SQLite:** persists inspection metadata between restarts.
- **Docker:** packages the runtime; a Dockerfile is not evidence of cloud deployment.

## Explain your contribution honestly

This package was generated with AI assistance. Run it, trace the code, and make a change you understand before presenting it. Useful extensions include your own real labeled dataset, a per-product model configuration, or a more rigorous validation report. Do not claim that you independently wrote every line or that synthetic test scores represent a deployed industrial system.
