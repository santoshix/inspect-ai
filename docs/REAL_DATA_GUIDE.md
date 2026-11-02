# Moving from a synthetic demo to real products

The bundled model has learned dark marks on generated gray textures. It will not reliably inspect arbitrary phones, clothing, circuit boards or industrial components. Model code is reusable; its training domain is not universal.

## Choose a narrow inspection task

Start with one product, one camera viewpoint, and a clear definition of a defect. Include good products with harmless scratches, reflections and lighting differences so the model does not simply learn “dark object = defect.” Obtain permission for the photographs and annotations you use.

## Annotate and split

Use an annotation tool that exports YOLO object-detection labels. Draw a box around each defect and start with a single class `surface_defect`. Clean images have empty `.txt` files. Each label line is:

```text
class_id center_x center_y width height
```

Coordinates are normalized by image width/height to the range 0–1. Keep images from the same physical item, video, or production batch in the same split. A random split of nearly identical frames produces misleadingly high results.

Create `real_data/images/train`, `real_data/images/val`, `real_data/images/test` and corresponding `labels` directories. Put this in `real_data/dataset.yaml`:

```yaml
train: images/train
val: images/val
test: images/test
names:
  0: surface_defect
```

## Train

Back up the included checkpoint and its evaluation report before retraining; the training command replaces the deployed checkpoint. A higher input resolution helps small real defects but requires more compute:

```powershell
.\.venv-inspect\Scripts\python.exe -m scripts.train --data real_data/dataset.yaml --model yolov8n.pt --imgsz 640 --epochs 60 --device cpu
```

`yolov8n.pt` requests pretrained weights and may download them. A suitable GPU can accelerate training when configured with a compatible GPU PyTorch build. The default package is CPU-only.

The provided inference service is deliberately fixed to 128 pixels for the synthetic model. **Before serving your 640-pixel model**, change the `imgsz=128` calls in `inspection/engine.py` to the resolution you validated, update its model label and notice, and replace the synthetic-specific model report. Do not leave synthetic test metrics beside a new real-data model. The synthetic evaluation script is specifically for the bundled benchmark, not a generic real-data evaluator.

## Evaluate before release

Use the validation set to choose a confidence threshold based on the relative cost of missed defects and false alarms. Freeze the model and threshold before the final test. Use Ultralytics `model.val(data=..., split='test', imgsz=640)` for real-data detection metrics. Separately measure image-level false negatives, false positives, latency, and failure cases by product/batch. Keep the test report and exact checkpoint hash together.

The project includes a usable local inference app, not a factory acceptance standard. Real deployment additionally needs access controls, request limits, observability, backups, load testing and human review procedures appropriate to the application.
