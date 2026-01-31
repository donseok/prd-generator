"""Unit tests for input validation utilities.

Tests filename validation, file size checks, extension filtering,
magic-number signature verification, and document count limits.
All tests are pure unit tests with no network or AI dependencies.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.exceptions import InputValidationError


# ---------------------------------------------------------------------------
# Helper: mock settings used by all validation functions
# ---------------------------------------------------------------------------

def _make_settings(**overrides):
    """Create a mock Settings object with sensible defaults."""
    defaults = {
        "max_file_size_mb": 50,
        "max_total_upload_mb": 200,
        "max_document_count": 20,
        "max_filename_length": 255,
    }
    defaults.update(overrides)
    settings = MagicMock()
    for k, v in defaults.items():
        setattr(settings, k, v)
    return settings


# We patch get_settings at the module level so every call inside
# app.utils.validation uses our mock instead of the real config.
SETTINGS_PATH = "app.utils.validation.get_settings"


# ---------------------------------------------------------------------------
# validate_filename
# ---------------------------------------------------------------------------

class TestValidateFilename:
    def test_valid_filename_passes(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            result = validate_filename("report.txt")
            assert result == "report.txt"

    def test_path_traversal_blocked(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            with pytest.raises(InputValidationError):
                validate_filename("../../etc/passwd")

    def test_null_bytes_handled(self):
        """Null bytes are stripped; if the rest is a clean basename it should pass."""
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            # After stripping null bytes "file\x00name.txt" becomes "filename.txt"
            result = validate_filename("file\x00name.txt")
            assert "\x00" not in result

    def test_empty_name_rejected(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            with pytest.raises(InputValidationError):
                validate_filename("")

    def test_whitespace_only_rejected(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            with pytest.raises(InputValidationError):
                validate_filename("   ")

    def test_overly_long_name_rejected(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings(max_filename_length=10)):
            with pytest.raises(InputValidationError):
                validate_filename("a" * 11 + ".txt")

    def test_dangerous_characters_rejected(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            with pytest.raises(InputValidationError):
                validate_filename("file<name>.txt")

    def test_extension_only_not_rejected_by_filename_validator(self):
        """os.path.splitext('.txt') -> ('.txt', ''), so the name_without_ext
        is '.txt' which is truthy. The filename validator allows this;
        extension validation is handled by validate_file_extension separately."""
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            result = validate_filename(".txt")
            assert result == ".txt"

    def test_slash_in_name_rejected(self):
        from app.utils.validation import validate_filename
        with patch(SETTINGS_PATH, return_value=_make_settings()):
            with pytest.raises(InputValidationError):
                validate_filename("path/file.txt")


# ---------------------------------------------------------------------------
# validate_file_size
# ---------------------------------------------------------------------------

class TestValidateFileSize:
    def test_within_limit_passes(self):
        from app.utils.validation import validate_file_size
        with patch(SETTINGS_PATH, return_value=_make_settings(max_file_size_mb=50)):
            # 10 MB is fine
            validate_file_size(10 * 1024 * 1024)

    def test_over_limit_raises(self):
        from app.utils.validation import validate_file_size
        with patch(SETTINGS_PATH, return_value=_make_settings(max_file_size_mb=1)):
            with pytest.raises(InputValidationError):
                validate_file_size(2 * 1024 * 1024)  # 2 MB > 1 MB limit

    def test_total_size_within_limit(self):
        from app.utils.validation import validate_file_size
        with patch(SETTINGS_PATH, return_value=_make_settings(max_file_size_mb=50, max_total_upload_mb=200)):
            validate_file_size(1 * 1024 * 1024, total_size=100 * 1024 * 1024)

    def test_total_size_over_limit_raises(self):
        from app.utils.validation import validate_file_size
        with patch(SETTINGS_PATH, return_value=_make_settings(max_file_size_mb=50, max_total_upload_mb=200)):
            with pytest.raises(InputValidationError):
                validate_file_size(1 * 1024 * 1024, total_size=201 * 1024 * 1024)


# ---------------------------------------------------------------------------
# validate_file_extension
# ---------------------------------------------------------------------------

class TestValidateFileExtension:
    def test_allowed_extension_passes(self):
        from app.utils.validation import validate_file_extension
        ext = validate_file_extension("photo.png")
        assert ext == ".png"

    def test_allowed_extension_case_insensitive(self):
        from app.utils.validation import validate_file_extension
        ext = validate_file_extension("document.PDF")
        assert ext == ".pdf"

    def test_disallowed_exe_raises(self):
        from app.utils.validation import validate_file_extension
        with pytest.raises(InputValidationError):
            validate_file_extension("malware.exe")

    def test_disallowed_bat_raises(self):
        from app.utils.validation import validate_file_extension
        with pytest.raises(InputValidationError):
            validate_file_extension("script.bat")

    def test_disallowed_sh_raises(self):
        from app.utils.validation import validate_file_extension
        with pytest.raises(InputValidationError):
            validate_file_extension("deploy.sh")

    def test_no_extension_raises(self):
        from app.utils.validation import validate_file_extension
        with pytest.raises(InputValidationError):
            validate_file_extension("README")


# ---------------------------------------------------------------------------
# validate_file_signature
# ---------------------------------------------------------------------------

class TestValidateFileSignature:
    def test_matching_png_signature_passes(self):
        from app.utils.validation import validate_file_signature
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        validate_file_signature(png_content, ".png")  # should not raise

    def test_matching_jpeg_signature_passes(self):
        from app.utils.validation import validate_file_signature
        jpeg_content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        validate_file_signature(jpeg_content, ".jpg")

    def test_matching_pdf_signature_passes(self):
        from app.utils.validation import validate_file_signature
        pdf_content = b"%PDF-1.7" + b"\x00" * 100
        validate_file_signature(pdf_content, ".pdf")

    def test_mismatched_signature_raises(self):
        from app.utils.validation import validate_file_signature
        # Claim it is PNG but provide JPEG bytes
        jpeg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        with pytest.raises(InputValidationError):
            validate_file_signature(jpeg_bytes, ".png")

    def test_unknown_extension_skips_validation(self):
        from app.utils.validation import validate_file_signature
        # .txt has no signature defined; should pass silently
        validate_file_signature(b"Hello, world!", ".txt")

    def test_empty_content_raises(self):
        from app.utils.validation import validate_file_signature
        with pytest.raises(InputValidationError):
            validate_file_signature(b"", ".png")


# ---------------------------------------------------------------------------
# validate_document_count
# ---------------------------------------------------------------------------

class TestValidateDocumentCount:
    def test_valid_count_passes(self):
        from app.utils.validation import validate_document_count
        with patch(SETTINGS_PATH, return_value=_make_settings(max_document_count=20)):
            validate_document_count(5)  # should not raise

    def test_zero_raises(self):
        from app.utils.validation import validate_document_count
        with patch(SETTINGS_PATH, return_value=_make_settings(max_document_count=20)):
            with pytest.raises(InputValidationError):
                validate_document_count(0)

    def test_over_max_raises(self):
        from app.utils.validation import validate_document_count
        with patch(SETTINGS_PATH, return_value=_make_settings(max_document_count=5)):
            with pytest.raises(InputValidationError):
                validate_document_count(6)
