
import time
import sys
import os

# Mock requests before importing backend
from unittest.mock import MagicMock
sys.modules["requests"] = MagicMock()

# Add backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from bullbear_backend.data import DataFetcher, DataType
from bullbear_backend.data.types import DataResult

# Mock source to avoid actual network calls and verify cache hits
class MockSource:
    def __init__(self, value):
        self.value = value
        self.call_count = 0

    def fetch(self):
        self.call_count += 1
        return DataResult(
            data_type=DataType.BTC_PRICE,
            value=self.value,
            provider="mock"
        )

def test_cache():
    print("Testing DataFetcher Cache...")
    fetcher = DataFetcher()
    
    # Monkey patch _get_source to return our mock
    mock_source = MockSource(100.0)
    original_get_source = fetcher._get_source
    fetcher._get_source = lambda dt: mock_source
    
    try:
        # First call - should hit source
        print("1. Initial fetch...")
        result1 = fetcher.get(DataType.BTC_PRICE)
        assert result1.value == 100.0
        assert mock_source.call_count == 1
        print("   -> OK (Hit source)")

        # Second call - should hit cache
        print("2. Second fetch (immediate)...")
        result2 = fetcher.get(DataType.BTC_PRICE)
        assert result2.value == 100.0
        assert mock_source.call_count == 1  # count should still be 1
        print("   -> OK (Hit cache)")

        # Verify class level persistence
        print("3. New instance fetch...")
        fetcher2 = DataFetcher()
        # Monkey patch new instance too (though it shouldn't matter for the cache check if it hits cache first)
        fetcher2._get_source = lambda dt: mock_source 
        
        result3 = fetcher2.get(DataType.BTC_PRICE)
        assert result3.value == 100.0
        assert mock_source.call_count == 1 # Shared cache, count stays 1
        print("   -> OK (Shared class cache)")

        # Wait for TTL expirations (simulated)
        print("4. Testing TTL expiry...")
        # Manually manipulate the cache timestamp to expire it
        # _CACHE is {DataType: (timestamp, result)}
        old_ts = time.time() - 301 # 5 minutes + 1 second ago
        fetcher._CACHE[DataType.BTC_PRICE] = (old_ts, result1)
        
        result4 = fetcher.get(DataType.BTC_PRICE)
        assert mock_source.call_count == 2 # Should increment now
        print("   -> OK (Cache expired, hit source)")

    finally:
        # Restore
        fetcher._get_source = original_get_source

if __name__ == "__main__":
    try:
        test_cache()
        print("\nAll cache tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
