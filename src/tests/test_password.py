"""Tests for password hashing and validation utilities."""

from src.app.auth.password import (
    hash_password,
    verify_password,
    validate_password_strength,
    needs_rehash
)


class TestPasswordUtils:
    """Test password hashing and validation utilities."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # Should be different from original

    def test_hash_password_unique_salts(self):
        """Test that each password gets a unique salt."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts should produce different hashes

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self):
        """Test verifying against invalid hash."""
        password = "TestPassword123!"
        invalid_hash = "not-a-valid-hash"

        assert verify_password(password, invalid_hash) is False

    def test_validate_password_strength_valid(self):
        """Test validating a strong password."""
        password = "TestPassword123!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_password_strength_too_short(self):
        """Test validating a password that's too short."""
        password = "Test1!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "at least 8 characters long" in " ".join(errors)

    def test_validate_password_strength_no_uppercase(self):
        """Test validating a password without uppercase letters."""
        password = "testpassword123!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "uppercase letter" in " ".join(errors)

    def test_validate_password_strength_no_lowercase(self):
        """Test validating a password without lowercase letters."""
        password = "TESTPASSWORD123!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "lowercase letter" in " ".join(errors)

    def test_validate_password_strength_no_numbers(self):
        """Test validating a password without numbers."""
        password = "TestPassword!"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "number" in " ".join(errors)

    def test_validate_password_strength_no_special_chars(self):
        """Test validating a password without special characters."""
        password = "TestPassword123"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert "special character" in " ".join(errors)

    def test_validate_password_strength_multiple_issues(self):
        """Test validating a weak password with multiple issues."""
        password = "weak"
        is_valid, errors = validate_password_strength(password)

        assert is_valid is False
        assert len(errors) > 1

    def test_needs_rehash_valid_hash(self):
        """Test checking if a valid hash needs rehashing."""
        password = "TestPassword123!"
        hashed = hash_password(password)

        # Fresh hash shouldn't need rehashing
        assert needs_rehash(hashed) is False

    def test_needs_rehash_invalid_hash(self):
        """Test checking if an invalid hash needs rehashing."""
        invalid_hash = "not-a-valid-hash"

        # Invalid hash should definitely need rehashing
        assert needs_rehash(invalid_hash) is True
