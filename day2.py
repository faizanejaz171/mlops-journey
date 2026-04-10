import os
import csv
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image


def scan_image_folder(folder_path: str) -> list[dict]:
    """
    Scan a folder for images. Return a list of dicts
    with metadata for each file found.
    """
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    results = []

    for img_path in sorted(folder.rglob("*")):
        if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.bmp']:
            continue

        try:
            img = Image.open(img_path)
            w, h = img.size
            size_kb = round(img_path.stat().st_size / 1024, 2)
            aspect = round(w / h, 2) if h != 0 else 0

            results.append({
                "filename": img_path.name,
                "folder": str(img_path.parent),
                "width_px": w,
                "height_px": h,
                "aspect_ratio": aspect,
                "size_kb": size_kb,
                "format": img.format,
                "mode": img.mode,       # RGB, RGBA, L (grayscale), etc.
                "status": "ok"
            })

        except Exception as e:
            results.append({
                "filename": img_path.name,
                "folder": str(img_path.parent),
                "width_px": 0,
                "height_px": 0,
                "aspect_ratio": 0,
                "size_kb": 0,
                "format": "unknown",
                "mode": "unknown",
                "status": f"error: {e}"
            })

    return results


def save_csv(results: list[dict], output_path: str):
    """Save results list to a CSV file."""
    if not results:
        print("No results to save.")
        return

    fieldnames = results[0].keys()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved: {output_path}")


def print_summary(results: list[dict]):
    """Print a human-readable summary to terminal."""
    total = len(results)
    ok = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] != "ok"]

    print("\n" + "="*45)
    print(f"  IMAGE SCAN REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*45)
    print(f"  Total files found : {total}")
    print(f"  Valid images      : {len(ok)}")
    print(f"  Errors/corrupt    : {len(errors)}")

    if ok:
        sizes = [r["size_kb"] for r in ok]
        widths = [r["width_px"] for r in ok]
        heights = [r["height_px"] for r in ok]

        print(f"\n  Size (KB):")
        print(f"    Min: {min(sizes)}   Max: {max(sizes)}")
        print(f"    Avg: {round(sum(sizes)/len(sizes), 1)}")
        print(f"\n  Dimensions:")
        print(f"    Width  — Min: {min(widths)}px  Max: {max(widths)}px")
        print(f"    Height — Min: {min(heights)}px  Max: {max(heights)}px")

        modes = {}
        for r in ok:
            modes[r["mode"]] = modes.get(r["mode"], 0) + 1
        print(f"\n  Colour modes: {modes}")

    if errors:
        print(f"\n  Errors:")
        for e in errors:
            print(f"    {e['filename']}: {e['status']}")

    print("="*45 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scan image folder and produce a CSV report."
    )
    parser.add_argument(
        "--input", required=True,
        help="Folder containing images to scan"
    )
    parser.add_argument(
        "--output", default="scan_report.csv",
        help="Output CSV path (default: scan_report.csv)"
    )
    args = parser.parse_args()

    results = scan_image_folder(args.input)
    print_summary(results)
    save_csv(results, args.output)
