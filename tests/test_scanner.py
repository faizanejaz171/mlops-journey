import sys
from pathlib import Path

import pytest
from PIL import Image

# Add parent folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from scanner import scan_folder, scan_single_image

# ===== FIXTURES (test data generators) =====

@pytest.fixture
def valid_image_file(tmp_path):
    """Create a valid test image (200x150 PNG)."""
    img_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (200, 150), color="red")
    img.save(img_path)
    return img_path


@pytest.fixture
def corrupt_image_file(tmp_path):
    """Create a corrupt (fake) image file."""
    img_path = tmp_path / "fake.jpg"
    img_path.write_text("this is not an image")
    return img_path


@pytest.fixture
def image_folder(tmp_path):
    """Create folder with 3 valid + 1 corrupt image."""
    folder = tmp_path / "test_images"
    folder.mkdir()

    # 3 valid images
    for i in range(3):
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(folder / f"valid_{i}.png")

    # 1 corrupt image
    (folder / "corrupt.jpg").write_text("fake data")

    return folder


# ===== TEST CLASSES =====

class TestScanSingleImage:
    """Tests for the scan_single_image function."""

    def test_valid_image_returns_ok_status(self, valid_image_file):
        result = scan_single_image(valid_image_file)
        assert result["status"] == "ok"
        assert result["error"] is None

    def test_valid_image_returns_correct_dimensions(self, valid_image_file):
        result = scan_single_image(valid_image_file)
        assert result["width_px"] == 200
        assert result["height_px"] == 150

    def test_valid_image_returns_correct_filename(self, valid_image_file):
        result = scan_single_image(valid_image_file)
        assert result["filename"] == "test_image.png"

    def test_valid_image_returns_positive_size(self, valid_image_file):
        result = scan_single_image(valid_image_file)
        assert result["size_kb"] > 0

    def test_valid_image_calculates_aspect_ratio(self, valid_image_file):
        result = scan_single_image(valid_image_file)
        expected = round(200 / 150, 2)
        assert result["aspect_ratio"] == expected

    def test_corrupt_image_returns_error_status(self, corrupt_image_file):
        result = scan_single_image(corrupt_image_file)
        assert result["status"] == "error"
        assert result["error"] is not None
        assert len(result["error"]) > 0

    def test_corrupt_image_returns_zero_dimensions(self, corrupt_image_file):
        result = scan_single_image(corrupt_image_file)
        assert result["width_px"] == 0
        assert result["height_px"] == 0

    def test_corrupt_image_does_not_raise_exception(self, corrupt_image_file):
        try:
            _ = scan_single_image(corrupt_image_file)
        except Exception as e:
            pytest.fail(f"scan_single_image raised an exception: {e}")


class TestScanFolder:
    """Tests for the scan_folder function."""

    def test_folder_returns_correct_total_count(self, image_folder):
        results = scan_folder(str(image_folder))
        assert len(results) == 4   # 3 valid + 1 corrupt

    def test_folder_counts_valid_images(self, image_folder):
        results = scan_folder(str(image_folder))
        ok = [r for r in results if r["status"] == "ok"]
        assert len(ok) == 3

    def test_folder_counts_errors(self, image_folder):
        results = scan_folder(str(image_folder))
        errors = [r for r in results if r["status"] == "error"]
        assert len(errors) == 1

    def test_empty_folder_returns_empty_list(self, tmp_path):
        results = scan_folder(str(tmp_path))
        assert results == []

    def test_missing_folder_raises_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            scan_folder("/this/path/does/not/exist")
