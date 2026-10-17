#!/usr/bin/env python3
"""Текстура плана без фиолетовых стрелок движения и лиловых линий — для референсов рендера.
Пиксели пурпурных оттенков заменяются медианой соседних обычных пикселей."""
import sys, numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert('RGB'); a = np.asarray(im).astype(int)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
mask = (r > 120) & (b > 120) & (g < 0.88 * np.minimum(r, b)) & (abs(r - b) < 90)   # magenta / purple
mask = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).filter(__import__('PIL.ImageFilter', fromlist=['MaxFilter']).MaxFilter(5))) > 0
out = a.copy(); ys, xs = np.nonzero(mask)
H, W = mask.shape
for y, x in zip(ys, xs):
    y0, y1, x0, x1 = max(0, y - 6), min(H, y + 7), max(0, x - 6), min(W, x + 7)
    win = a[y0:y1, x0:x1][~mask[y0:y1, x0:x1]]
    out[y, x] = np.median(win, axis=0) if len(win) else (250, 222, 223)
Image.fromarray(out.astype(np.uint8)).save(dst, quality=92)
print('cleaned', mask.sum(), 'px ->', dst)
