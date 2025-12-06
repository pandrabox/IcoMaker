# Icomaker

Icomaker creates 256x256 icon PNGs from PNG images placed in `img/`.

Behavior
- Reads all PNGs from `img/` folder (same directory as `Icomaker.py`).
- If an image has transparent margins, they will be trimmed.
- The resulting image is padded to be square — the original is centered — with a transparent background.
- The square image is resized to 256x256 (default) and written into `icons/`.

Usage

- Windows (double-click): run `Icomaker.bat` — it calls `Icomaker.py` with the same arguments.
- CLI:

```powershell
# Install requirements in your Python environment
python -m pip install -r requirements.txt

# Run with default directories:
python Icomaker.py

# Run with custom source or destination and overwrite existing
python Icomaker.py --src img --dst icons --overwrite

# Change output size (e.g., 128)
python Icomaker.py --size 128
```

Notes
- `Icomaker.py` attempts to preserve alpha/transparency.
- If an image has no alpha channel, the script treats it as opaque and still centers/pads/resizes it.

License: MIT (do what you like)
