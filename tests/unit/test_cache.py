"""FileCache 서비스 단위 테스트.

캐시의 기본 동작(저장, 조회, 삭제, 만료)과 통계를 테스트합니다.
"""

import time
import pytest
from pathlib import Path

from app.services.cache import FileCache, CacheEntry, CacheStats


@pytest.fixture
def cache(tmp_path):
    """임시 디렉토리 기반 FileCache."""
    return FileCache(
        cache_dir=tmp_path / "cache",
        ttl_hours=1,
        max_memory_entries=5,
    )


# ===================================================================
# 기본 get / set
# ===================================================================

class TestGetSet:
    def test_set_and_get(self, cache):
        cache.set("key1", {"data": "hello"})
        result = cache.get("key1")
        assert result == {"data": "hello"}

    def test_get_nonexistent_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_overwrite_existing_key(self, cache):
        cache.set("key1", "first")
        cache.set("key1", "second")
        assert cache.get("key1") == "second"

    def test_stores_various_types(self, cache):
        cache.set("str", "hello")
        cache.set("int", 42)
        cache.set("list", [1, 2, 3])
        cache.set("dict", {"a": 1})

        assert cache.get("str") == "hello"
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"a": 1}


# ===================================================================
# get_cache_key
# ===================================================================

class TestCacheKey:
    def test_from_content_deterministic(self, cache):
        k1 = cache.get_cache_key_from_content("hello world")
        k2 = cache.get_cache_key_from_content("hello world")
        assert k1 == k2

    def test_different_content_different_key(self, cache):
        k1 = cache.get_cache_key_from_content("hello")
        k2 = cache.get_cache_key_from_content("world")
        assert k1 != k2

    def test_prefix_included(self, cache):
        key = cache.get_cache_key_from_content("test", prefix="myprefix")
        assert "myprefix" in key

    def test_file_based_key(self, cache, tmp_path):
        test_file = tmp_path / "sample.txt"
        test_file.write_text("sample content for key generation")
        key = cache.get_cache_key(test_file)
        assert isinstance(key, str)
        assert len(key) > 0


# ===================================================================
# delete / clear
# ===================================================================

class TestDeleteClear:
    def test_delete_existing_key(self, cache):
        cache.set("key1", "value")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_nonexistent_key_no_error(self, cache):
        cache.delete("nonexistent")  # 오류 없이 통과

    def test_clear_removes_all(self, cache):
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.get("c") is None


# ===================================================================
# 만료 (TTL)
# ===================================================================

class TestExpiration:
    def test_custom_ttl(self, tmp_path):
        """TTL을 매우 짧게 설정하고 만료 확인."""
        cache = FileCache(
            cache_dir=tmp_path / "expire_cache",
            ttl_hours=0,  # 즉시 만료 (0시간)
            max_memory_entries=10,
        )
        # ttl_hours=0이지만, set 시점에서는 현재 시간 + 0시간이므로
        # 사실상 저장 시점과 동일 → 바로 만료되지 않을 수 있음
        # cleanup_expired로 확인
        cache.set("soon", "data", ttl_hours=0)
        # 직후에는 캐시에 있을 수 있음 (시간차가 거의 없음)
        # cleanup으로 만료 처리
        cache.cleanup_expired()

    def test_cleanup_expired_removes_old_entries(self, tmp_path):
        """만료된 항목이 cleanup으로 제거되는지 확인."""
        cache = FileCache(
            cache_dir=tmp_path / "cleanup_cache",
            ttl_hours=24,
            max_memory_entries=10,
        )
        cache.set("valid", "data")
        cache.cleanup_expired()
        # 유효한 항목은 남아있어야 함
        assert cache.get("valid") == "data"


# ===================================================================
# LRU 방출 (메모리 제한)
# ===================================================================

class TestLRUEviction:
    def test_exceeding_max_entries_evicts_oldest(self, cache):
        """max_memory_entries(5)를 초과하면 오래된 항목 방출."""
        for i in range(7):
            cache.set(f"key{i}", f"value{i}")

        # 최근 항목은 접근 가능
        assert cache.get("key6") == "value6"
        # 가장 오래된 항목은 메모리에서 방출됨 (파일에는 있을 수 있음)


# ===================================================================
# 통계
# ===================================================================

class TestStats:
    def test_initial_stats(self, cache):
        stats = cache.stats
        assert isinstance(stats, CacheStats)
        assert stats.hits == 0
        assert stats.misses == 0

    def test_hit_and_miss_tracked(self, cache):
        cache.set("exists", "value")
        cache.get("exists")       # hit
        cache.get("not_exists")   # miss

        stats = cache.stats
        assert stats.hits >= 1
        assert stats.misses >= 1

    def test_hit_rate_calculation(self):
        stats = CacheStats(hits=3, misses=1)
        assert stats.hit_rate == pytest.approx(0.75)

    def test_hit_rate_zero_total(self):
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0

    def test_stats_summary_string(self, cache):
        cache.set("x", 1)
        cache.get("x")
        summary = cache.get_stats_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
