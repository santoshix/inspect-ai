"""Inspect a local folder and write annotated images plus a JSON report."""
import argparse
import base64
import json
from pathlib import Path
from inspection.engine import Detector,decode_image

def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path)
    parser.add_argument('--output',type=Path,default=Path('runtime/batch'))
    parser.add_argument('--threshold',type=float,default=.35);args=parser.parse_args()
    if not args.folder.is_dir(): parser.error('Input folder does not exist')
    args.output.mkdir(parents=True,exist_ok=True);detector=Detector();rows=[]
    for path in sorted(args.folder.iterdir()):
        if path.suffix.lower() not in ('.png','.jpg','.jpeg'):continue
        try:
            result=detector.inspect(decode_image(path.read_bytes()),args.threshold)
            encoded=result.pop('annotated_image').split(',',1)[1]
            (args.output/(path.name+'.annotated.png')).write_bytes(base64.b64decode(encoded))
            rows.append({'filename':path.name,**result})
        except ValueError as exc: rows.append({'filename':path.name,'error':str(exc)})
    (args.output/'results.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    print(f'Processed {len(rows)} files. Results: {args.output.resolve()}')

if __name__=='__main__':main()
