# Model card

**Model:** YOLOv8n, one-class object detector using PyTorch and Ultralytics.

**Initialization:** architecture YAML, randomly initialized; no pretrained COCO checkpoint used for the shipped model.

**Training:** requested 40 epochs, seed 42, 128-pixel images, CPU. Best checkpoint selected using validation performance. Actual per-epoch values are in `reports/training_history.csv`; model metadata is in `models/metadata.json`.

**Data:** 720 original synthetic images: 480 training, 120 validation, 120 test. Textured grayscale backgrounds contain zero or more generated dark lines/ellipses. Independent random streams produce the splits; tests verify no byte-identical images cross splits. Sample thumbnails use a separate random stream. There are no human subjects or downloaded third-party photographs.

**Labels:** `surface_defect`, with axis-aligned bounding boxes. Good images have empty label files. Defect types are visually varied but share one label.

**Use:** a reproducible educational demonstration of model training, box localization, an inference API, dashboard, persistence, evaluation and tests.

**Do not use for:** real product release decisions, safety certification, medical inspection or unvalidated general object detection. A detector with no boxes has not proven that a product is defect-free.

**Metrics:** measured held-out results are in `reports/evaluation.json`. mAP@50 and mAP@50:95 refer to bounding boxes. Image-level precision/recall use confidence 0.35 and NMS IoU 0.45. Detection precision/recall from Ultralytics use its best-F1 operating point. Inference timing measures warmed CPU `predict` calls and excludes HTTP, decoding, drawing and persistence. Dashboard time uses the same prediction-call boundary but can vary with image size and hardware.

**Limitations:** simple same-generator synthetic validation; small input resolution; uncalibrated scores; substantial domain shift to real photos; possible missed faint, tiny, reflective or low-contrast defects. High synthetic scores cannot establish performance on actual manufacturing products.

**Reproducibility:** code, generation seeds, labels, checkpoint, dependency versions, training history and SHA-256 hash are provided. Exact retraining outputs may differ across hardware/library versions.

**Runtime:** local single-process CPU inference, serialized predictor access. User image pixels are held in memory and returned, not stored. Metadata is stored in SQLite. Only load checkpoints obtained from trusted sources.
