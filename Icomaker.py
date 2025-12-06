#!/usr/bin/env python3
"""
Icomaker.py

Finds PNGs in ./img, trims transparent margins, pads to a square (centered), resizes to 256x256,
and writes results as PNGs into ./icons.

Usage:
    python Icomaker.py [--src img] [--dst icons] [--size 256] [--overwrite]

Requirements: pillow
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Tuple

from PIL import Image


DEFAULT_SIZE = 256


def get_alpha_bbox(image: Image.Image) -> Tuple[int, int, int, int] | None:
    """Return the bounding box (l, upper, r, lower) of areas where alpha > 0.

    If image has no alpha channel, return the image bbox (0,0,w,h). If
    the image is fully transparent, return None.
    """
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        alpha = image.convert("RGBA").split()[-1]
        bbox = alpha.getbbox()
        return bbox
    else:
        # No alpha channel — the image is treated as fully opaque
        return (0, 0, image.width, image.height)


def trim_image(img: Image.Image) -> Image.Image:
    bbox = get_alpha_bbox(img)
    if bbox is None:
        # fully transparent -> return original
        return img
    if bbox == (0, 0, img.width, img.height):
        return img
    return img.crop(bbox)


def pad_to_square(img: Image.Image, background=(0, 0, 0, 0)) -> Image.Image:
    width, height = img.size
    size = max(width, height)

    # Ensure RGBA so we preserve alpha for transparent background
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Create a square background and paste centered
    new_im = Image.new("RGBA", (size, size), background)
    upper_left = ((size - width) // 2, (size - height) // 2)
    new_im.paste(img, upper_left, img if img.mode == "RGBA" else None)
    return new_im


def process_image(src_path: Path, dst_path: Path, size: int = DEFAULT_SIZE):
    print(f"Processing {src_path} -> {dst_path}")
    img = Image.open(src_path)

    # Convert paletted images with transparency correctly
    if img.mode == "P":
        img = img.convert("RGBA")

    # Trim transparent margins
    trimmed = trim_image(img)

    # Pad to square with transparent background
    squared = pad_to_square(trimmed)

    # Resize to desired size
    resized = squared.resize((size, size), Image.LANCZOS)

    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PNG preserving transparency
    resized.save(dst_path, "PNG")


def find_pngs(folder: Path):
    if not folder.exists():
        return []
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".png"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create 256x256 icons from PNGs in ./img")
    parser.add_argument("--src", type=str, default="img", help="Source folder with PNGs (default: img)")
    parser.add_argument("--dst", type=str, default="icons", help="Destination folder for PNGs (default: icons)")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="Output size (square, default: 256)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing icons")
    parser.add_argument("--quiet", action="store_true", help="Suppress informational printing")
    return parser.parse_args()


def main():
    args = parse_args()
    src_dir = Path(args.src)
    dst_dir = Path(args.dst)

    pngs = find_pngs(src_dir)
    if not args.quiet:
        print(f"Found {len(pngs)} PNG files in {src_dir}")
        print(f"Output will be placed into: {dst_dir}")

    if not pngs:
        return 0

    for p in pngs:
        target = dst_dir / p.name
        if target.exists() and not args.overwrite:
            if not args.quiet:
                print(f"Skipping {p.name} (exists). Use --overwrite to replace.")
            continue

        try:
            process_image(p, target, size=args.size)
        except Exception as e:
            print(f"Failed to process {p}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
