"""Train YOLO on synthetic or user-provided YOLO-format data."""
import argparse
import json
import shutil
from pathlib import Path
import yaml
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]

def resolve_dataset(source):
    source=Path(source).resolve()
    config=yaml.safe_load(source.read_text(encoding='utf-8'))
    if 'path' not in config: config['path']=str(source.parent)
    elif not Path(config['path']).is_absolute(): config['path']=str((source.parent/config['path']).resolve())
    ROOT.joinpath('runtime').mkdir(exist_ok=True)
    target=ROOT/'runtime'/'resolved_dataset.yaml'
    target.write_text(yaml.safe_dump(config),encoding='utf-8')
    return target

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=ROOT/'data/dataset.yaml')
    parser.add_argument('--model',default='yolov8n.yaml',help='YAML trains from scratch; .pt fine-tunes trusted weights')
    parser.add_argument('--epochs',type=int,default=40)
    parser.add_argument('--imgsz',type=int,default=128)
    parser.add_argument('--device',default='cpu')
    args=parser.parse_args()
    model=YOLO(args.model)
    model.train(data=str(resolve_dataset(args.data)),epochs=args.epochs,imgsz=args.imgsz,device=args.device,
                batch=32,workers=0,seed=42,deterministic=True,project=str(ROOT/'runs'),name='defects',
                exist_ok=True,patience=12,plots=False,amp=False,cache=True,verbose=False,
                mosaic=.2,close_mosaic=5,translate=.05,scale=.2,fliplr=.5,hsv_h=0,hsv_s=0,hsv_v=.15)
    ROOT.joinpath('models').mkdir(exist_ok=True)
    shutil.copy2(model.trainer.best,ROOT/'models/defect_yolo.pt')
    metadata={'architecture':'YOLOv8n','initialization':args.model,'epochs_requested':args.epochs,
              'image_size':args.imgsz,'training_seed':42,'data_yaml':args.data.name,
              'scope':'Synthetic surface textures only, unless retrained on a different dataset.'}
    (ROOT/'models/metadata.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print('Saved models/defect_yolo.pt. Run python -m scripts.evaluate next.')

if __name__=='__main__': main()
