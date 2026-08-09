"""Security-focused validation and configuration tests."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.validators import (
    detect_image_type,
    sanitize_filename,
    validate_image_content,
)


def test_jwt_secret_rejected_in_production():
    with pytest.raises(ValidationError):
        Settings(debug=False, jwt_secret="dev-secret-change-in-production")


def test_jwt_secret_requires_min_length_in_production():
    with pytest.raises(ValidationError):
        Settings(debug=False, jwt_secret="short-secret")


def test_jwt_secret_allowed_in_debug():
    s = Settings(debug=True, jwt_secret="dev-secret-change-in-production")
    assert s.jwt_secret == "dev-secret-change-in-production"


def test_seed_demo_data_defaults_to_debug():
    assert Settings(debug=True).seed_demo_data is True
    prod_secret = "a" * 32
    assert Settings(debug=False, seed_demo_data=False, jwt_secret=prod_secret).seed_demo_data is False


def test_sanitize_filename_strips_path_traversal():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("../../../secret.txt") == "secret.txt"
    assert "\x00" not in sanitize_filename("evil\x00.jpg")


def test_sanitize_filename_empty_returns_uuid():
    name = sanitize_filename("")
    assert name.endswith(".jpg")
    assert len(name) > 10


def test_detect_image_type_jpeg():
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert detect_image_type(jpeg) == ("image/jpeg", ".jpg")


def test_detect_image_type_rejects_non_image():
    assert detect_image_type(b"not an image file") is None


def test_validate_image_content_rejects_spoofed_type():
    fake = b"not an image"
    with pytest.raises(ValueError, match="valid JPEG"):
        validate_image_content(fake, "image/jpeg")
