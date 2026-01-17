#!/usr/bin/env python3
"""
Icomaker.py

Finds PNGs in ./img, trims transparent margins, pads to a square (centered), resizes to 256x256,
and writes results as PNGs into ./icons.

Usage:
    python Icomaker.py [--src img] [--dst icons] [--size 256] [--overwrite] [--tolerance 0]

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


def make_background_transparent(img: Image.Image, tolerance: int = 0) -> Image.Image:
    """左上1pxの色を取得し、その色（と類似色）を透明にする。
    
    Args:
        img: 入力画像
        tolerance: 色の許容差（0=完全一致のみ、大きいほど曖昧に判定）
    
    Returns:
        背景を透明にした画像
    """
    # RGBAに変換
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    
    # 左上1pxの色を取得
    bg_color = img.getpixel((0, 0))
    
    # 既に透明なら何もしない
    if len(bg_color) == 4 and bg_color[3] == 0:
        print(f"  左上ピクセルは既に透明です。スキップします。")
        return img
    
    print(f"  背景色検出: RGBA{bg_color}, 許容差: {tolerance}")
    
    # ピクセルデータを取得
    pixels = img.load()
    width, height = img.size
    changed_count = 0
    
    for y in range(height):
        for x in range(width):
            current = pixels[x, y]
            # RGB部分の差を計算
            diff = sum(abs(current[i] - bg_color[i]) for i in range(3))
            
            if diff <= tolerance * 3:  # tolerance は各チャンネルあたりの許容差
                pixels[x, y] = (current[0], current[1], current[2], 0)
                changed_count += 1
    
    print(f"  透過ピクセル数: {changed_count} / {width * height}")
    return img


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


def process_image(src_path: Path, dst_path: Path, size: int = DEFAULT_SIZE, tolerance: int = 0):
    print(f"Processing {src_path} -> {dst_path}")
    img = Image.open(src_path)

    # Convert paletted images with transparency correctly
    if img.mode == "P":
        img = img.convert("RGBA")

    # 背景色を透明にする（左上1pxが不透明な場合）
    img = make_background_transparent(img, tolerance)

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
    parser.add_argument("--tolerance", type=int, default=0, help="背景色の許容差 (0=完全一致, default: 0)")
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
            process_image(p, target, size=args.size, tolerance=args.tolerance)
        except Exception as e:
            print(f"Failed to process {p}: {e}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
