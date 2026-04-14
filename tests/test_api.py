import io
import sys
from pathlib import Path

import pytest
from PIL import Image

# Add parent folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import your FastAPI app (adjust import as per your file structure)
from fastapi.testclient import TestClient

from api import app  # or from main import app, or whatever your file is named

# ===== FIXTURES =====

@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_image_bytes():
    """Create fake PNG image as bytes (100x80)."""
    img = Image.new("RGB", (100, 80), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def image_folder(tmp_path):
    """Create folder with 3 valid + 1 corrupt image."""
    folder = tmp_path / "test_images"
    folder.mkdir()

    # 3 valid images
    for i in range(3):
        img = Image.new("RGB", (100, 100), color="green")
        img.save(folder / f"valid_{i}.png")

    # 1 corrupt image
    (folder / "corrupt.jpg").write_text("fake data")

    return str(folder)  # Return as string for URL parameter


# ===== TEST CLASSES =====

class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_service_name(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "image-scanner"

    def test_health_response_is_json(self, client):
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"


class TestScanUploadEndpoint:
    """Tests for POST /scan/upload"""

    def test_valid_png_returns_200(self, client, valid_image_bytes):
        response = client.post(
            "/scan/upload",
            files={"file": ("photo.png", valid_image_bytes, "image/png")},
        )
        assert response.status_code == 200

    def test_valid_png_returns_ok_status(self, client, valid_image_bytes):
        response = client.post(
            "/scan/upload",
            files={"file": ("photo.png", valid_image_bytes, "image/png")},
        )
        data = response.json()
        assert data["status"] == "ok"

    def test_valid_png_returns_correct_dimensions(self, client, valid_image_bytes):
        response = client.post(
            "/scan/upload",
            files={"file": ("photo.png", valid_image_bytes, "image/png")},
        )
        data = response.json()
        assert data["width_px"] == 100
        assert data["height_px"] == 80

    def test_valid_png_preserves_filename(self, client, valid_image_bytes):
        response = client.post(
            "/scan/upload",
            files={"file": ("my_photo.png", valid_image_bytes, "image/png")},
        )
        data = response.json()
        assert data["filename"] == "my_photo.png"

    def test_unsupported_file_type_returns_400(self, client):
        response = client.post(
            "/scan/upload",
            files={"file": ("doc.txt", b"some text content", "text/plain")},
        )
        assert response.status_code == 400

    def test_unsupported_file_type_returns_error_message(self, client):
        response = client.post(
            "/scan/upload",
            files={"file": ("doc.pdf", b"pdf content", "application/pdf")},
        )
        data = response.json()
        assert "detail" in data
        assert len(data["detail"]) > 0

    def test_corrupt_image_returns_200_with_error_status(self, client):
        response = client.post(
            "/scan/upload",
            files={"file": ("broken.jpg", b"not image bytes", "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_response_contains_all_required_fields(self, client, valid_image_bytes):
        response = client.post(
            "/scan/upload",
            files={"file": ("photo.png", valid_image_bytes, "image/png")},
        )
        data = response.json()
        required = {
            "filename", "width_px", "height_px",
            "aspect_ratio", "size_kb", "format",
            "mode", "status", "error"
        }
        assert required.issubset(data.keys())


class TestScanFolderEndpoint:
    """Tests for GET /scan/folder"""

    def test_valid_folder_returns_200(self, client, image_folder):
        response = client.get(f"/scan/folder?path={image_folder}")
        assert response.status_code == 200

    def test_valid_folder_returns_correct_total(self, client, image_folder):
        response = client.get(f"/scan/folder?path={image_folder}")
        data = response.json()
        assert data["total"] == 4

    def test_valid_folder_counts_ok_and_errors(self, client, image_folder):
        response = client.get(f"/scan/folder?path={image_folder}")
        data = response.json()
        assert data["ok"] == 3
        assert data["errors"] == 1

    def test_valid_folder_returns_results_list(self, client, image_folder):
        response = client.get(f"/scan/folder?path={image_folder}")
        data = response.json()
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 4

    def test_missing_folder_returns_404(self, client):
        response = client.get("/scan/folder?path=/does/not/exist")
        assert response.status_code == 404

    def test_missing_folder_returns_detail_message(self, client):
        response = client.get("/scan/folder?path=/does/not/exist")
        data = response.json()
        assert "detail" in data
