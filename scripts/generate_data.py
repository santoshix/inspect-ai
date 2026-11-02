"""Generate original synthetic textures and YOLO boxes, never real factory data."""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def sample(rng, size=128):
    # Shared background distribution for clean and defective samples.
    base = rng.uniform(140, 205)
    yy, xx = np.mgrid[:size, :size]
    texture = base + rng.normal(0, 3, (size, size))
    texture += rng.uniform(1, 5) * np.sin(yy / rng.uniform(1, 4))
    texture += (xx / size - .5) * rng.uniform(-25, 25)
    gray = np.clip(texture, 0, 255).astype(np.uint8)
    image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    boxes = []
    if rng.random() < .7:
        for _ in range(int(rng.integers(1, 4))):
            mask = np.zeros((size, size), np.uint8)
            x, y = rng.integers(12, size-12, 2)
            kind = int(rng.integers(0, 3))
            if kind == 0:
                x2 = int(np.clip(x + rng.integers(-45, 46), 5, size-6))
                y2 = int(np.clip(y + rng.integers(-45, 46), 5, size-6))
                cv2.line(mask, (int(x), int(y)), (x2, y2), 255, int(rng.integers(2, 6)))
            else:
                cv2.ellipse(mask, (int(x), int(y)), (int(rng.integers(4, 13)), int(rng.integers(4, 13))),
                            float(rng.uniform(0, 180)), 0, 360, 255, -1)
            image[mask > 0] = int(rng.integers(15, 85))
            px, py, w, h = cv2.boundingRect(mask)
            x1, y1 = max(0, px-2), max(0, py-2)
            x2, y2 = min(size, px+w+2), min(size, py+h+2)
            boxes.append([x1, y1, x2, y2])
    return image, boxes

def generate(output=ROOT/'data', counts=(480, 120, 120), seed=42):
    output = Path(output)
    summary = {'description': 'Original procedurally generated synthetic metal textures; one class: surface_defect.',
               'seed': seed, 'image_size': 128, 'splits': {}}
    for split, count, offset in zip(('train','val','test'), counts, (0,10000,20000)):
        rng = np.random.default_rng(seed+offset)
        images, labels = output/'images'/split, output/'labels'/split
        images.mkdir(parents=True, exist_ok=True); labels.mkdir(parents=True, exist_ok=True)
        # Each regeneration replaces this generated split, preventing stale examples.
        for folder, pattern in ((images,'*.png'), (labels,'*.txt')):
            for old in folder.glob(pattern): old.unlink()
        clean, defects = 0, 0
        for i in range(count):
            image, boxes = sample(rng)
            clean += not bool(boxes); defects += len(boxes)
            name = f'{split}_{i:04d}'
            cv2.imwrite(str(images/f'{name}.png'), image)
            lines = [f'0 {(x1+x2)/256:.7f} {(y1+y2)/256:.7f} {(x2-x1)/128:.7f} {(y2-y1)/128:.7f}'
                     for x1,y1,x2,y2 in boxes]
            (labels/f'{name}.txt').write_text('\n'.join(lines), encoding='utf-8')
        summary['splits'][split] = {'images': count, 'clean_images': clean, 'defect_boxes': defects}
    # Relative paths keep the ZIP portable between Windows, Linux, and Docker.
    (output/'dataset.yaml').write_text('train: images/train\nval: images/val\ntest: images/test\nnames:\n  0: surface_defect\n', encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=ROOT/'data')
    parser.add_argument('--seed',type=int,default=42); args=parser.parse_args()
    print(json.dumps(generate(args.output,seed=args.seed),indent=2))
