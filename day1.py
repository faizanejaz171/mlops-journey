import os
import sys
from pathlib import Path

from PIL import Image


def scan_image_folder(folder_path):
    folder = Path(folder_path)
    results = []

    if not folder.exists():
        print(f"Error: Folder '{folder}' does not exist")
        sys.exit(1)

    for img_path in folder.rglob("*"):
        if img_path.suffix.lower() not in ['.jpg','.jpeg','.png','.webp','.bmp']:
            continue
        try:
            img = Image.open(img_path)
            w, h = img.size
            size_kb = round(img_path.stat().st_size / 1024, 1)
            results.append({
                "file": str(img_path),
                "width": w,
                "height": h,
                "size_kb": size_kb,
                "status": "ok"
            })
        except Exception as e:
            results.append({
                "file": str(img_path),
                "width": 0,
                "height": 0,
                "size_kb": 0,
                "status": f"error: {e}"
            })

    return results

if __name__ == "__main__":
    # Use environment variable or default
    folder = os.getenv("IMAGE_FOLDER", "/home/faizan/Documents/mlops-journey/day-1/images")

    data = scan_image_folder(folder)

    print(f"\nFound {len(data)} images in: {folder}\n")
    for row in data:
        status_icon = "✓" if row['status'] == 'ok' else "✗"
        print(f"{status_icon} {row['file']}")
        print(f"   {row['width']}x{row['height']} | {row['size_kb']} KB | {row['status']}\n")
