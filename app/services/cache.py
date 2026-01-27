"""
캐시(Cache) 서비스입니다.
자주 사용되는 데이터나 계산 결과를 임시로 저장해두어 속도를 높이는 역할을 합니다.

기능:
1. 같은 파일을 다시 처리할 때 저장된 결과를 사용 (시간 절약)
2. 메모리와 파일 두 곳에 저장하여 프로그램이 꺼져도 데이터 유지
3. 오래된 데이터는 자동으로 삭제 (기본 24시간)
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
    """캐시에 저장되는 데이터 단위입니다."""
    value: Any  # 실제 저장할 데이터
    created_at: float  # 생성된 시간
    expires_at: float  # 만료되는 시간 (이 시간 이후에는 삭제됨)
    hit_count: int = 0  # 얼마나 자주 조회되었는지 카운트


@dataclass
class CacheStats:
    """캐시 성능 통계입니다."""
    hits: int = 0  # 캐시에서 성공적으로 데이터를 찾은 횟수
    misses: int = 0  # 캐시에 없어서 새로 처리해야 했던 횟수
    evictions: int = 0  # 꽉 차거나 오래돼서 삭제된 횟수

    @property
    def hit_rate(self) -> float:
        """적중률 계산 (성공 횟수 / 전체 시도 횟수)"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class FileCache:
    """
    파일을 이용한 캐시 저장소입니다.
    
    작동 원리:
    - 데이터의 '지문'(해시)을 만들어서 이름표로 사용합니다.
    - 메모리(RAM)에 먼저 저장하고, 디스크(파일)에도 백업합니다.
    - 데이터를 찾을 때는 메모리 -> 디스크 순서로 찾아봅니다.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_hours: int = 24,
        max_memory_entries: int = 100,
    ):
        """
        초기화 함수.

        Args:
            cache_dir: 캐시 파일을 저장할 폴더 위치
            ttl_hours: 데이터 유효 시간 (시간 단위, 기본 24시간)
            max_memory_entries: 메모리에 저장할 최대 개수 (넘으면 오래된 것부터 삭제)
        """
        if cache_dir is None:
            # 기본적으로 프로젝트 폴더 내 .cache/prd_generator 에 저장
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / ".cache" / "prd_generator"

        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.max_memory_entries = max_memory_entries

        # 메모리 캐시 저장소 (딕셔너리)
        self._memory_cache: Dict[str, CacheEntry] = {}

        # 통계 정보
        self._stats = CacheStats()

        # 폴더 만들기
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[FileCache] 초기화 완료: {self.cache_dir}, 유지시간={ttl_hours}시간")

    def get_cache_key(self, file_path: Path) -> str:
        """
        파일을 식별하는 고유한 키(Key)를 생성합니다.
        
        파일명과 파일 내용의 일부를 섞어서 만듭니다.
        파일 내용이 조금이라도 바뀌면 키도 바뀝니다.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 파일 내용을 읽어서 MD5 해시 생성
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        content_hash = hasher.hexdigest()[:12]

        # 파일명 + 해시값 조합
        safe_name = file_path.stem.replace(" ", "_")[:20]
        return f"{safe_name}_{content_hash}"

    def get_cache_key_from_content(self, content: str, prefix: str = "content") -> str:
        """텍스트 내용으로 키를 생성합니다."""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{prefix}_{content_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 데이터를 꺼내옵니다.
        
        순서:
        1. 메모리 확인 -> 있으면 반환
        2. 파일 확인 -> 있으면 메모리에 올리고 반환
        3. 없으면 None 반환
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
                # 유효기간 지난 데이터 삭제
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
                    # 다음에 빨리 찾기 위해 메모리에도 저장
                    self._set_memory_cache(key, value, data["expires_at"])
                    self._stats.hits += 1
                    logger.debug(f"[FileCache] 파일 캐시 히트: {key}")
                    return value
                else:
                    # 유효기간 지난 파일 삭제
                    cache_file.unlink(missing_ok=True)
                    self._stats.evictions += 1

            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"[FileCache] 캐시 파일 손상됨: {key}, {e}")
                cache_file.unlink(missing_ok=True)

        self._stats.misses += 1
        logger.debug(f"[FileCache] 캐시 미스 (데이터 없음): {key}")
        return None

    def set(self, key: str, value: Any, ttl_hours: Optional[int] = None) -> None:
        """
        데이터를 캐시에 저장합니다.
        메모리와 파일 양쪽에 저장합니다.
        """
        now = time.time()
        ttl = ttl_hours if ttl_hours is not None else self.ttl_hours
        expires_at = now + (ttl * 3600)  # 시간 -> 초 변환

        # 메모리에 저장
        self._set_memory_cache(key, value, expires_at)

        # 파일에 저장
        cache_file = self._get_cache_file_path(key)
        try:
            data = {
                "value": value,
                "created_at": now,
                "expires_at": expires_at,
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            logger.debug(f"[FileCache] 캐시 저장됨: {key}")

        except (TypeError, IOError) as e:
            logger.warning(f"[FileCache] 파일 저장 실패: {key}, {e}")

    def delete(self, key: str) -> bool:
        """특정 데이터를 캐시에서 삭제합니다."""
        deleted = False

        # 메모리에서 삭제
        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True

        # 파일에서 삭제
        cache_file = self._get_cache_file_path(key)
        if cache_file.exists():
            cache_file.unlink()
            deleted = True

        if deleted:
            logger.debug(f"[FileCache] 삭제됨: {key}")

        return deleted

    def clear(self) -> int:
        """모든 캐시 데이터를 지웁니다 (초기화)."""
        count = len(self._memory_cache)

        # 메모리 비우기
        self._memory_cache.clear()

        # 파일들 지우기
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                pass

        logger.info(f"[FileCache] 전체 초기화: {count}개 삭제")
        return count

    def cleanup_expired(self) -> int:
        """유효기간이 지난 오래된 데이터들만 정리합니다."""
        now = time.time()
        count = 0

        # 메모리 정리
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if now >= entry.expires_at
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            count += 1

        # 파일 정리
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if now >= data.get("expires_at", 0):
                    cache_file.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                # 파일이 깨졌으면 삭제
                cache_file.unlink(missing_ok=True)
                count += 1

        if count > 0:
            logger.info(f"[FileCache] 만료된 캐시 정리: {count}개")

        return count

    @property
    def stats(self) -> CacheStats:
        """현재 통계 정보를 반환합니다."""
        return self._stats

    def get_stats_summary(self) -> str:
        """통계 요약 텍스트"""
        return (
            f"성공: {self._stats.hits}, "
            f"실패: {self._stats.misses}, "
            f"성공률: {self._stats.hit_rate:.1%}, "
            f"메모리 사용중: {len(self._memory_cache)}개"
        )

    def _get_cache_file_path(self, key: str) -> Path:
        """키에 해당하는 파일 경로를 만듭니다."""
        # 파일명에 쓸 수 없는 문자 교체
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _set_memory_cache(self, key: str, value: Any, expires_at: float) -> None:
        """메모리에 데이터를 저장합니다. 너무 많으면 옛날 것을 지웁니다 (LRU)."""
        # 꽉 찼으면 가장 오래된 것 삭제
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
    """FileCache 인스턴스를 하나만 생성해서 반환합니다."""
    global _file_cache
    if _file_cache is None:
        _file_cache = FileCache()
    return _file_cache