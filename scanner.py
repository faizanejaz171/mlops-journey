from pathlib import Path
from PIL import Image


def scan_single_image(img_path: Path) -> dict:
    """
    Scan one image file. Returns a dict with metadata.
    Handles errors — never raises exceptions to the caller.
    """
    try:
        img = Image.open(img_path)
        w, h = img.size
        return {
            "filename": img_path.name,
            "width_px": w,
            "height_px": h,
            "aspect_ratio": round(w / h, 2) if h != 0 else 0,
            "size_kb": round(img_path.stat().st_size / 1024, 2),
            "format": img.format or "unknown",
            "mode": img.mode,
            "status": "ok",
            "error": None,
        }
    except Exception as e:
        return {
            "filename": img_path.name,
            "width_px": 0,
            "height_px": 0,
            "aspect_ratio": 0,
            "size_kb": 0,
            "format": "unknown",
            "mode": "unknown",
            "status": "error",
            "error": str(e),
        }


def scan_folder(folder_path: str) -> list[dict]:
    """
    Scan all images in a folder recursively.
    Returns list of result dicts.
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    results = []
    extensions = {".jpg", ".jpeg", ".png", ".bmp"}

    for img_path in sorted(folder.rglob("*")):
        if img_path.suffix.lower() in extensions:
            results.append(scan_single_image(img_path))

    return results
