import mlflow.pyfunc
import pandas as pd
from scanner import scan_single_image

# 1. Point to your LOCAL MLflow
mlflow.set_tracking_uri("http://localhost:5000")

# 2. Load the Production model once when the file starts
print("Loading model from local registry...")
model = mlflow.pyfunc.load_model("models:/image-quality-classifier/Production")

def predict_quality(image_path):
    # Scan the image to get width, height, blur, etc.
    features = scan_single_image(image_path)
    
    if features.get("status") == "error":
         return {"quality": "unknown", "error": features.get("error")}

    # Put the features into a Pandas DataFrame for the model
    df = pd.DataFrame([{
        "width": features.get("width", 0),
        "height": features.get("height", 0),
        "size_kb": features.get("size_kb", 0),
        "blur_score": features.get("blur_score", 0),
        "brightness": features.get("brightness", 0),
        "aspect_ratio": features.get("aspect_ratio", 0)
    }])

    # Ask the model to predict (1 = Good, 0 = Bad)
    prediction = model.predict(df)[0]
    
    return {
        "quality": "good" if prediction == 1 else "bad",
        "features": features
    }
