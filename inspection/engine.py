"""Load the bundled YOLO checkpoint once and serialize access to its predictor."""
import base64
import io
import threading
import time
import warnings
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 16_000_000

def decode_image(raw):
    if not raw: raise ValueError('Upload a PNG or JPEG image.')
    if len(raw) > MAX_BYTES: raise ValueError('Image exceeds the 8 MB upload limit.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                if source.format not in ('PNG','JPEG'): raise ValueError('Only PNG and JPEG images are supported.')
                if source.width * source.height > MAX_PIXELS: raise ValueError('Image exceeds 16 megapixels.')
                if min(source.size) < 16: raise ValueError('Image must be at least 16 pixels on each side.')
                image=ImageOps.exif_transpose(source).convert('RGB')
                image.thumbnail((1600,1600))
                return cv2.cvtColor(np.array(image),cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('Cannot decode image. Choose an intact PNG or JPEG.') from exc

class Detector:
    def __init__(self, weights=None):
        self.path=Path(weights or ROOT/'models/defect_yolo.pt')
        if not self.path.is_file():
            raise FileNotFoundError('Missing model. Restore models/defect_yolo.pt or run python -m scripts.train.')
        self.model=YOLO(str(self.path))
        self.lock=threading.Lock()
        self.model.predict(np.zeros((128,128,3),np.uint8),imgsz=128,device='cpu',verbose=False)

    def inspect(self,image,threshold=.35):
        if not .05 <= threshold <= .95: raise ValueError('Confidence threshold must be between 0.05 and 0.95.')
        with self.lock:
            started=time.perf_counter()
            result=self.model.predict(image,imgsz=128,conf=threshold,iou=.45,device='cpu',verbose=False,max_det=100)[0]
            elapsed=(time.perf_counter()-started)*1000
        detections=[]
        canvas=image.copy()
        h,w=image.shape[:2]
        for box in result.boxes:
            x1,y1,x2,y2=[int(round(v)) for v in box.xyxy[0].tolist()]
            x1,x2=max(0,min(w-1,x1)),max(0,min(w-1,x2))
            y1,y2=max(0,min(h-1,y1)),max(0,min(h-1,y2))
            confidence=float(box.conf[0]); name=result.names[int(box.cls[0])]
            detections.append({'label':name,'confidence':round(confidence,4),'box':[x1,y1,x2,y2]})
            cv2.rectangle(canvas,(x1,y1),(x2,y2),(80,110,255),max(1,w//400))
        ok,encoded=cv2.imencode('.png',canvas)
        if not ok: raise RuntimeError('Failed to encode result image')
        return {'status':'DEFECT DETECTED' if detections else 'NO DEFECT DETECTED',
                'detections':detections,'defect_count':len(detections),
                'max_confidence':max((d['confidence'] for d in detections),default=0),
                'threshold':threshold,'inference_ms':round(elapsed,2),'width':w,'height':h,
                'coordinate_space':'displayed image after EXIF orientation and resizing to at most 1600 px',
                'annotated_image':'data:image/png;base64,'+base64.b64encode(encoded).decode(),
                'model':'YOLOv8n / synthetic surface defects',
                'notice':'Demo model trained on synthetic textures. A negative prediction does not certify product quality.'}
