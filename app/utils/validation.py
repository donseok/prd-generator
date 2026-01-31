"""입력 유효성 검증 유틸리티.

파일 업로드 시 보안 및 무결성 검증을 수행합니다.
"""

import os
import re
from typing import Optional

from app.config import get_settings
from app.exceptions import InputValidationError


# 허용된 파일 확장자 목록
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".json",
    ".csv", ".xlsx", ".xls",
    ".pptx", ".ppt",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
    ".pdf", ".docx", ".doc",
    ".eml", ".msg",
}

# 매직 넘버 기반 파일 시그니처 (확장자 → 시그니처 바이트)
FILE_SIGNATURES = {
    ".png": b"\x89PNG",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".gif": b"GIF8",
    ".bmp": b"BM",
    ".pdf": b"%PDF",
    ".xlsx": b"PK",          # ZIP-based (Office Open XML)
    ".pptx": b"PK",          # ZIP-based (Office Open XML)
    ".docx": b"PK",          # ZIP-based (Office Open XML)
    ".xls": b"\xd0\xcf\x11", # OLE2 compound document
    ".ppt": b"\xd0\xcf\x11",
    ".doc": b"\xd0\xcf\x11",
}

# 위험한 파일명 패턴
DANGEROUS_PATTERNS = re.compile(r"[<>:\"|?*\x00-\x1f]")


def validate_filename(filename: str) -> str:
    """
    파일명 유효성 검증.

    - 경로 순회 공격 방지 (../, / 등)
    - 널 바이트 제거
    - 위험 문자 검사
    - 길이 제한

    Args:
        filename: 원본 파일명

    Returns:
        정리된 안전한 파일명

    Raises:
        InputValidationError: 유효하지 않은 파일명
    """
    settings = get_settings()

    if not filename or not filename.strip():
        raise InputValidationError("파일명이 비어있습니다")

    # 널 바이트 제거
    cleaned = filename.replace("\x00", "")

    # 경로 순회 방지
    basename = os.path.basename(cleaned)
    if basename != cleaned or ".." in cleaned:
        raise InputValidationError(
            f"잘못된 파일명입니다: 경로 순회가 감지되었습니다",
            details={"filename": filename},
        )

    # 위험 문자 검사
    if DANGEROUS_PATTERNS.search(basename):
        raise InputValidationError(
            f"파일명에 허용되지 않는 문자가 포함되어 있습니다",
            details={"filename": filename},
        )

    # 길이 제한
    if len(basename) > settings.max_filename_length:
        raise InputValidationError(
            f"파일명이 너무 깁니다 (최대 {settings.max_filename_length}자)",
            details={"filename": basename, "length": len(basename)},
        )

    # 빈 이름 방지 (확장자만 있는 경우)
    name_without_ext = os.path.splitext(basename)[0]
    if not name_without_ext:
        raise InputValidationError(
            "파일명이 비어있습니다 (확장자만 존재)",
            details={"filename": basename},
        )

    return basename


def validate_file_size(
    file_size: int,
    total_size: Optional[int] = None,
) -> None:
    """
    파일 크기 검증.

    Args:
        file_size: 개별 파일 크기 (bytes)
        total_size: 전체 업로드 누적 크기 (bytes, 선택)

    Raises:
        InputValidationError: 크기 제한 초과
    """
    settings = get_settings()
    max_bytes = settings.max_file_size_mb * 1024 * 1024

    if file_size > max_bytes:
        raise InputValidationError(
            f"파일 크기가 제한을 초과했습니다 (최대 {settings.max_file_size_mb}MB)",
            details={
                "file_size_bytes": file_size,
                "max_size_bytes": max_bytes,
            },
        )

    if total_size is not None:
        max_total = settings.max_total_upload_mb * 1024 * 1024
        if total_size > max_total:
            raise InputValidationError(
                f"전체 업로드 크기가 제한을 초과했습니다 (최대 {settings.max_total_upload_mb}MB)",
                details={
                    "total_size_bytes": total_size,
                    "max_total_bytes": max_total,
                },
            )


def validate_file_extension(filename: str) -> str:
    """
    파일 확장자 검증.

    Args:
        filename: 파일명

    Returns:
        소문자로 변환된 확장자 (예: ".png")

    Raises:
        InputValidationError: 허용되지 않는 확장자
    """
    ext = os.path.splitext(filename)[1].lower()

    if not ext:
        raise InputValidationError(
            "파일에 확장자가 없습니다",
            details={"filename": filename},
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise InputValidationError(
            f"허용되지 않는 파일 형식입니다: {ext}",
            details={
                "extension": ext,
                "allowed": sorted(ALLOWED_EXTENSIONS),
            },
        )

    return ext


def validate_file_signature(content: bytes, extension: str) -> None:
    """
    매직 넘버 기반 파일 내용 검증.

    파일의 처음 몇 바이트가 확장자에 맞는 시그니처인지 확인합니다.
    시그니처가 정의되지 않은 확장자는 검증을 건너뜁니다.

    Args:
        content: 파일 바이너리 내용
        extension: 소문자 확장자 (예: ".png")

    Raises:
        InputValidationError: 시그니처 불일치
    """
    expected = FILE_SIGNATURES.get(extension)
    if expected is None:
        return  # 시그니처가 정의되지 않은 타입은 건너뜀

    if not content or len(content) < len(expected):
        raise InputValidationError(
            f"파일 내용이 비어있거나 손상되었습니다",
            details={"extension": extension},
        )

    if not content[:len(expected)].startswith(expected):
        raise InputValidationError(
            f"파일 내용이 확장자({extension})와 일치하지 않습니다",
            details={"extension": extension},
        )


def validate_document_count(count: int) -> None:
    """
    업로드 문서 수 제한 검증.

    Args:
        count: 업로드하려는 문서 수

    Raises:
        InputValidationError: 문서 수 초과
    """
    settings = get_settings()

    if count < 1:
        raise InputValidationError("최소 1개 이상의 파일을 업로드해야 합니다")

    if count > settings.max_document_count:
        raise InputValidationError(
            f"한 번에 업로드 가능한 최대 문서 수를 초과했습니다 (최대 {settings.max_document_count}개)",
            details={
                "count": count,
                "max_count": settings.max_document_count,
            },
        )
