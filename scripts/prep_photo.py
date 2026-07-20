#!/usr/bin/env python3
"""Prep a portrait photo for ASCII conversion.

  1. Remove the background (rembg) so the subject is isolated.
  2. Boost local contrast (CLAHE) so a flat face gets real highlights/shadows.
  3. Composite onto pure white so the background maps to blank (spaces).

Usage:  python scripts/prep_photo.py source-photo.jpg
Output: source-prepped.png  (grayscale)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUT = Path(__file__).resolve().parent.parent / "source-prepped.png"


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <photo>", file=sys.stderr)
        sys.exit(1)
    src = Path(sys.argv[1])
    img = Image.open(src).convert("RGBA")

    # 1. remove background
    cut = remove(img)

    # 2. composite onto pure white
    white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, cut).convert("L")

    # 3. CLAHE contrast boost
    arr = np.array(comp)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    Image.fromarray(arr).save(OUT)
    print(f"Wrote {OUT} ({comp.size[0]}x{comp.size[1]})")


if __name__ == "__main__":
    main()
