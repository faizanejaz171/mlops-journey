import io
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from scanner import scan_single_image, scan_folder


app = FastAPI(
    title="Image Scanner API",
    description="Scan images and get metadata as JSON.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    """
    Always returns OK. Used by load balancers and monitoring
    tools to verify the service is alive.
    """
    return {"status": "ok", "service": "image-scanner"}


@app.post("/scan/upload")
async def scan_uploaded_image(file: UploadFile = File(...)):
    """
    Accept an uploaded image file via HTTP POST.
    Returns metadata as JSON.

    Usage:
        curl -X POST http://localhost:8000/scan/upload \
             -F "file=@/path/to/image.jpg"
    """
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

    result = scan_single_image(tmp_path)
    result["filename"] = file.filename
    tmp_path.unlink(missing_ok=True)

    return JSONResponse(content=result)


@app.get("/scan/folder")
def scan_folder_endpoint(path: str):
    """
    Scan all images in a folder path on the server.
    Returns list of metadata dicts as JSON.

    Usage:
        curl "http://localhost:8000/scan/folder?path=/data/images"
    """
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
