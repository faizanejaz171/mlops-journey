import csv, random
from pathlib import Path
from PIL import Image
import numpy as np


def blur_score(img):
    a = np.array(img.convert("L"), dtype=float)
    lap = a[:-2,1:-1]+a[2:,1:-1]+a[1:-1,:-2]+a[1:-1,2:]-4*a[1:-1,1:-1]
    return float(np.var(lap))


def brightness(img):
    return float(np.array(img.convert("L")).mean())


def extract(path):
    try:
        img = Image.open(path)
        w, h = img.size
        return {
            "width": w, "height": h,
            "size_kb": round(path.stat().st_size/1024, 2),
            "blur_score": round(blur_score(img), 2),
            "brightness": round(brightness(img), 2),
            "aspect_ratio": round(w/h, 3) if h else 0,
        }
    except Exception:
        return None


def label(f):
    if f["width"] < 100 or f["height"] < 100: return 0
    if f["blur_score"] < 50: return 0
    if f["brightness"] < 30 or f["brightness"] > 240: return 0
    return 1


def synthetic(n=200):
    random.seed(42)
    rows = []
    for i in range(n):
        good = random.random() > 0.35
        rows.append({
            "width":        random.randint(200,1920) if good else random.randint(20,99),
            "height":       random.randint(200,1080) if good else random.randint(20,99),
            "size_kb":      round(random.uniform(30,500) if good else random.uniform(1,15),2),
            "blur_score":   round(random.uniform(100,800) if good else random.uniform(5,49),2),
            "brightness":   round(random.uniform(60,200) if good else random.uniform(5,29),2),
            "aspect_ratio": round(random.uniform(0.5,2.5),3),
            "label": 1 if good else 0, "filename": f"syn_{i}.jpg",
        })
    return rows


def generate_dataset(folder, output):
    rows = []
    for p in Path(folder).rglob("*"):
        if p.suffix.lower() not in {".jpg",".jpeg",".png"}: continue
        f = extract(p)
        if f:
            f["label"] = label(f)
            f["filename"] = p.name
            rows.append(f)
    if not rows:
        print("No images found — using synthetic data")
        rows = synthetic()
    with open(output,"w",newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    good = sum(1 for r in rows if r["label"]==1)
    print(f"Dataset: {len(rows)} rows → {output}")
    print(f"  Good: {good}  Bad: {len(rows)-good}")


if __name__ == "__main__":
    generate_dataset("./test_images", "ml/dataset.csv")
