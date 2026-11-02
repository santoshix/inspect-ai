"""Evaluate the frozen checkpoint once on held-out synthetic test images."""
import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
import cv2
import numpy as np
import torch
import ultralytics
from ultralytics import YOLO
from inspection.engine import ROOT
from scripts.train import resolve_dataset

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--threshold',type=float,default=.35)
    args=parser.parse_args()
    model=YOLO(str(ROOT/'models/defect_yolo.pt'))
    metrics=model.val(data=str(resolve_dataset(ROOT/'data/dataset.yaml')),split='test',imgsz=128,
                      device='cpu',batch=32,workers=0,plots=False,verbose=False,project=str(ROOT/'runs'),name='test',exist_ok=True)
    paths=sorted((ROOT/'data/images/test').glob('*.png'))
    tp=tn=fp=fn=0;times=[]
    model.predict(cv2.imread(str(paths[0])),imgsz=128,device='cpu',verbose=False)
    import time
    for path in paths:
        image=cv2.imread(str(path));started=time.perf_counter()
        result=model.predict(image,imgsz=128,conf=args.threshold,iou=.45,device='cpu',verbose=False)[0]
        times.append((time.perf_counter()-started)*1000)
        truth=bool((ROOT/'data/labels/test'/f'{path.stem}.txt').read_text().strip())
        pred=len(result.boxes)>0
        tp+=truth and pred;tn+=not truth and not pred;fp+=not truth and pred;fn+=truth and not pred
    report={'evaluated_at':datetime.now(timezone.utc).isoformat(),'dataset':'Original synthetic surface textures',
            'split':'test','test_images':len(paths),'threshold':args.threshold,
            'detection':{'mAP50':float(metrics.box.map50),'mAP50_95':float(metrics.box.map),
                         'precision_at_ultralytics_best_F1':float(metrics.box.mp),
                         'recall_at_ultralytics_best_F1':float(metrics.box.mr)},
            'image_level':{'true_positive':int(tp),'true_negative':int(tn),'false_positive':int(fp),'false_negative':int(fn),
                           'precision':tp/max(tp+fp,1),'recall':tp/max(tp+fn,1),'accuracy':(tp+tn)/len(paths)},
            'latency_ms':{'median':float(np.median(times)),'p95':float(np.percentile(times,95)),
                          'scope':'Warm CPU model.predict calls; excludes HTTP, decoding, drawing, and database writes'},
            'environment':{'python':platform.python_version(),'platform':platform.platform(),
                           'torch':torch.__version__,'ultralytics':ultralytics.__version__},
            'model_sha256':hashlib.sha256((ROOT/'models/defect_yolo.pt').read_bytes()).hexdigest(),
            'limitations':['Synthetic images from the same generator as training; not evidence of real factory accuracy.',
                            'One class: surface_defect. No material identification or defect subtype classification.',
                            'Confidence scores are not calibrated probabilities. No defect detected does not mean safe.',
                            'Threshold 0.35 fixed before test evaluation; test data not used for training/checkpoint selection.',
                            'Latency is machine dependent; high-resolution uploads are resized to a 128-pixel inference input.']}
    (ROOT/'reports').mkdir(exist_ok=True)
    (ROOT/'reports/evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
