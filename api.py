import tempfile
import os
from pathlib import Path
import pandas as pd
import mlflow.pyfunc
from ml.predictor import predict_quality
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from scanner import scan_folder, scan_single_image

# --- NEW: LOAD YOUR MLFLOW MODEL HERE ---
# Point to your local MLflow server
mlflow.set_tracking_uri("http://localhost:5000")

# Load the model tagged as "Production"
print("Loading ML model from Registry...")
model_uri = "models:/image-quality-classifier/Production"
model = mlflow.pyfunc.load_model(model_uri)
print("Model loaded successfully!")
# ----------------------------------------

app = FastAPI(
    title="Image Scanner API",
    description="Scan images and predict quality using MLflow.",
    version="1.0.0",
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "image-scanner"}

@app.post("/scan/upload")
async def scan_uploaded_image(file: UploadFile = File(...)):
    allowed = {".jpg", ".jpeg", ".png", ".bmp"}
    suffix = Path(file.filename).suffix.lower()

    if suffix not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {allowed}",
        )

    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    # 1. Extract the features using your existing scanner
    result = scan_single_image(tmp_path)
    result["filename"] = file.filename
    tmp_path.unlink(missing_ok=True)

    # --- NEW: MAKE THE AI PREDICTION ---
    # The model needs these exact features in a Pandas DataFrame
    features = ["width", "height", "size_kb", "blur_score", "brightness", "aspect_ratio"]
    
    # Create a 1-row table with the image's stats
    df = pd.DataFrame([{
        "width": result.get("width", 0),
        "height": result.get("height", 0),
        "size_kb": result.get("size_kb", 0),
        "blur_score": result.get("blur_score", 0),
        "brightness": result.get("brightness", 0),
        "aspect_ratio": result.get("aspect_ratio", 0)
    }])

    # Ask the model for a prediction (returns 1 for Good, 0 for Bad)
    prediction = model.predict(df)[0]
    
    # Add the human-readable AI verdict to the JSON response
    result["ai_quality_prediction"] = "Good Image" if prediction == 1 else "Bad Image"
    # -----------------------------------

    return JSONResponse(content=result)

@app.get("/scan/folder")
def scan_folder_endpoint(path: str):
    try:
        results = scan_folder(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ok_count = sum(1 for r in results if r["status"] == "ok")
    error_count = len(results) - ok_count

    return {
        "total": len(results),
        "ok": ok_count,
        "errors": error_count,
        "results": results,
    }


@app.post("/predict/quality")
async def predict_image_quality(file: UploadFile = File(...)):
    """Upload an image. Returns quality prediction from
    the Production model in the MLflow registry."""
    allowed = {".jpg",".jpeg",".png"}
    suffix  = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported: {suffix}")

    contents = await file.read()
    import tempfile # Make sure tempfile is imported at the top of api.py
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    result = predict_quality(tmp_path)
    result["filename"] = file.filename
    tmp_path.unlink(missing_ok=True)
    return JSONResponse(content=result)
