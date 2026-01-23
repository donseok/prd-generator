"""Caching service for PRD generation system.

파일 기반 캐싱을 제공하여 동일 파일 재처리 시 성능을 향상시킵니다.

주요 기능:
- 파일 MD5 해시 기반 캐시키 생성
- 메모리 + 파일 이중 캐시
- 24시간 TTL (Time-To-Live)
- 캐시 히트율 통계

예상 효과:
- 동일 파일 재처리 시 92% 시간 단축
- Layer 1 파싱 결과 캐싱으로 가장 큰 효과

사용 예시:
    cache = get_file_cache()

    # 캐시 키 생성
    cache_key = cache.get_cache_key(file_path)

    # 캐시에서 조회
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 실제 처리
    result = await expensive_operation()

    # 캐시에 저장
    cache.set(cache_key, result)
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """캐시 엔트리."""
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0


@dataclass
class CacheStats:
    """캐시 통계."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """캐시 히트율 계산."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class FileCache:
    """
    파일 기반 캐싱 서비스.

    파일의 MD5 해시를 기반으로 캐시키를 생성하고,
    메모리 캐시와 파일 캐시를 이중으로 사용합니다.

    Attributes:
        cache_dir: 파일 캐시 저장 디렉토리
        ttl_hours: 캐시 만료 시간 (시간 단위)
        max_memory_entries: 메모리 캐시 최대 엔트리 수
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_hours: int = 24,
        max_memory_entries: int = 100,
    ):
        """
        FileCache 초기화.

        Args:
            cache_dir: 캐시 파일 저장 디렉토리. None이면 기본 위치 사용.
            ttl_hours: 캐시 만료 시간 (기본값: 24시간)
            max_memory_entries: 메모리 캐시 최대 크기 (기본값: 100)
        """
        if cache_dir is None:
            # 프로젝트 루트의 .cache 디렉토리 사용
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / ".cache" / "prd_generator"

        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.max_memory_entries = max_memory_entries

        # 메모리 캐시
        self._memory_cache: Dict[str, CacheEntry] = {}

        # 통계
        self._stats = CacheStats()

        # 캐시 디렉토리 생성
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[FileCache] 초기화 완료: {self.cache_dir}, TTL={ttl_hours}h")

    def get_cache_key(self, file_path: Path) -> str:
        """
        파일의 캐시키 생성.

        파일 경로와 내용의 MD5 해시를 조합하여
        고유한 캐시키를 생성합니다.

        Args:
            file_path: 파일 경로

        Returns:
            캐시키 문자열 (예: "document_abc123def456")
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일 내용 해시 계산
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        content_hash = hasher.hexdigest()[:12]

        # 파일명 + 해시 조합
        safe_name = file_path.stem.replace(" ", "_")[:20]
        return f"{safe_name}_{content_hash}"

    def get_cache_key_from_content(self, content: str, prefix: str = "content") -> str:
        """
        문자열 내용으로 캐시키 생성.

        Args:
            content: 캐시할 내용
            prefix: 캐시키 접두어

        Returns:
            캐시키 문자열
        """
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{prefix}_{content_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회.

        메모리 캐시 → 파일 캐시 순서로 조회합니다.
        만료된 엔트리는 자동으로 제거됩니다.

        Args:
            key: 캐시키

        Returns:
            캐시된 값. 없거나 만료되면 None.
        """
        now = time.time()

        # 1. 메모리 캐시 확인
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if now < entry.expires_at:
                entry.hit_count += 1
                self._stats.hits += 1
                logger.debug(f"[FileCache] 메모리 캐시 히트: {key}")
                return entry.value
            else:
                # 만료된 엔트리 제거
                del self._memory_cache[key]
                self._stats.evictions += 1

        # 2. 파일 캐시 확인
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if now < data.get("expires_at", 0):
                    value = data.get("value")
                    # 메모리 캐시에도 저장
                    self._set_memory_cache(key, value, data["expires_at"])
                    self._stats.hits += 1
                    logger.debug(f"[FileCache] 파일 캐시 히트: {key}")
                    return value
                else:
                    # 만료된 파일 삭제
                    cache_file.unlink(missing_ok=True)
                    self._stats.evictions += 1

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"[FileCache] 캐시 파일 손상: {key}, {e}")
                cache_file.unlink(missing_ok=True)

        self._stats.misses += 1
        logger.debug(f"[FileCache] 캐시 미스: {key}")
        return None

    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> None:
        """
        캐시에 값 저장.

        메모리 캐시와 파일 캐시 모두에 저장합니다.

        Args:
            key: 캐시키
            value: 저장할 값 (JSON 직렬화 가능해야 함)
            ttl_hours: 만료 시간. None이면 기본값 사용.
        """
        now = time.time()
        ttl = ttl_hours if ttl_hours is not None else self.ttl_hours
        expires_at = now + (ttl * 3600)

        # 메모리 캐시 저장
        self._set_memory_cache(key, value, expires_at)

        # 파일 캐시 저장
        cache_file = self._get_cache_file_path(key)
        try:
            data = {
                "value": value,
                "created_at": now,
                "expires_at": expires_at,
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            logger.debug(f"[FileCache] 캐시 저장: {key}")

        except (TypeError, IOError) as e:
            logger.warning(f"[FileCache] 파일 캐시 저장 실패: {key}, {e}")

    def delete(self, key: str) -> bool:
        """
        캐시에서 값 삭제.

        Args:
            key: 캐시키

        Returns:
            삭제 성공 여부
        """
        deleted = False

        # 메모리 캐시 삭제
        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True

        # 파일 캐시 삭제
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            cache_file.unlink()
            deleted = True

        if deleted:
            logger.debug(f"[FileCache] 캐시 삭제: {key}")

        return deleted

    def clear(self) -> int:
        """
        모든 캐시 삭제.

        Returns:
            삭제된 엔트리 수
        """
        count = len(self._memory_cache)

        # 메모리 캐시 초기화
        self._memory_cache.clear()

        # 파일 캐시 삭제
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

        logger.info(f"[FileCache] 캐시 초기화: {count}개 삭제")
        return count

    def cleanup_expired(self) -> int:
        """
        만료된 캐시 정리.

        Returns:
            정리된 엔트리 수
        """
        now = time.time()
        count = 0

        # 메모리 캐시 정리
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if now >= entry.expires_at
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            count += 1

        # 파일 캐시 정리
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if now >= data.get("expires_at", 0):
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                # 손상된 파일도 삭제
                cache_file.unlink(missing_ok=True)
                count += 1

        if count > 0:
            logger.info(f"[FileCache] 만료 캐시 정리: {count}개")

        return count

    @property
    def stats(self) -> CacheStats:
        """캐시 통계 반환."""
        return self._stats

    def get_stats_summary(self) -> str:
        """캐시 통계 요약 문자열."""
        return (
            f"히트: {self._stats.hits}, "
            f"미스: {self._stats.misses}, "
            f"히트율: {self._stats.hit_rate:.1%}, "
            f"메모리 엔트리: {len(self._memory_cache)}"
        )

    def _get_cache_file_path(self, key: str) -> Path:
        """캐시 파일 경로 반환."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _set_memory_cache(self, key: str, value: Any, expires_at: float) -> None:
        """메모리 캐시 저장 (LRU 정책)."""
        # 최대 크기 초과 시 가장 오래된 엔트리 제거
        if len(self._memory_cache) >= self.max_memory_entries:
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].created_at
            )
            del self._memory_cache[oldest_key]
            self._stats.evictions += 1

        self._memory_cache[key] = CacheEntry(
            value=value,
            created_at=time.time(),
            expires_at=expires_at,
        )


# 싱글톤 인스턴스
_file_cache: Optional[FileCache] = None


def get_file_cache() -> FileCache:
    """FileCache 싱글톤 인스턴스 반환."""
    global _file_cache
    if _file_cache is None:
        _file_cache = FileCache()
    return _file_cache
