"""Unit tests for custom exception classes.

Tests the exception hierarchy, default error codes, message handling,
and details propagation for all custom exceptions in the PRD generation system.
"""

import pytest

from app.exceptions import (
    PRDGeneratorError,
    ParsingError,
    NormalizationError,
    ValidationError,
    GenerationError,
    StorageError,
    ClaudeClientError,
    InputValidationError,
)


class TestPRDGeneratorError:
    def test_base_error_attributes(self):
        err = PRDGeneratorError("Something failed", error_code="ERR_TEST", details={"key": "value"})
        assert err.message == "Something failed"
        assert err.error_code == "ERR_TEST"
        assert err.details == {"key": "value"}
        assert str(err) == "Something failed"

    def test_base_error_defaults(self):
        err = PRDGeneratorError("Minimal error")
        assert err.error_code == "ERR_UNKNOWN"
        assert err.details is None

    def test_is_exception_subclass(self):
        err = PRDGeneratorError("test")
        assert isinstance(err, Exception)


class TestSubclassErrorCodes:
    """Each subclass must carry its own default error_code."""

    def test_parsing_error_code(self):
        err = ParsingError("parse fail")
        assert err.error_code == "ERR_PARSE_001"
        assert err.message == "parse fail"
        assert isinstance(err, PRDGeneratorError)

    def test_normalization_error_code(self):
        err = NormalizationError("norm fail")
        assert err.error_code == "ERR_NORM_001"
        assert isinstance(err, PRDGeneratorError)

    def test_validation_error_code(self):
        err = ValidationError("validation fail")
        assert err.error_code == "ERR_VALID_001"
        assert isinstance(err, PRDGeneratorError)

    def test_generation_error_code(self):
        err = GenerationError("gen fail")
        assert err.error_code == "ERR_GEN_001"
        assert isinstance(err, PRDGeneratorError)

    def test_storage_error_code(self):
        err = StorageError("storage fail")
        assert err.error_code == "ERR_STORE_001"
        assert isinstance(err, PRDGeneratorError)

    def test_claude_client_error_code(self):
        err = ClaudeClientError("claude fail")
        assert err.error_code == "ERR_CLAUDE_001"
        assert isinstance(err, PRDGeneratorError)


class TestInputValidationError:
    def test_error_code(self):
        err = InputValidationError("bad input")
        assert err.error_code == "ERR_INPUT_001"
        assert isinstance(err, PRDGeneratorError)
        assert isinstance(err, Exception)

    def test_with_details_dict(self):
        details = {"filename": "evil.exe", "reason": "disallowed extension"}
        err = InputValidationError("Invalid file", details=details)
        assert err.details == details
        assert err.details["filename"] == "evil.exe"


class TestExceptionHierarchy:
    """All custom exceptions must be catchable as PRDGeneratorError and as Exception."""

    @pytest.mark.parametrize(
        "exc_cls,args",
        [
            (ParsingError, ("msg",)),
            (NormalizationError, ("msg",)),
            (ValidationError, ("msg",)),
            (GenerationError, ("msg",)),
            (StorageError, ("msg",)),
            (ClaudeClientError, ("msg",)),
            (InputValidationError, ("msg",)),
        ],
    )
    def test_catchable_as_base_and_builtin(self, exc_cls, args):
        err = exc_cls(*args)
        assert isinstance(err, PRDGeneratorError)
        assert isinstance(err, Exception)

        # Can be caught with except PRDGeneratorError
        with pytest.raises(PRDGeneratorError):
            raise err
