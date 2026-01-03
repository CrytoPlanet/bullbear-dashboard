#!/usr/bin/env python3
"""测试API是否正常工作"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bullbear_backend.data import DataFetcher, DataType

def test_api():
    """测试所有数据源"""
    print("=" * 50)
    print("测试免费API数据源")
    print("=" * 50)
    print()
    
    fetcher = DataFetcher()
    
    try:
        # 测试BTC价格
        print("1. 测试BTC价格...")
        result = fetcher.get(DataType.BTC_PRICE)
        print(f"   [OK] BTC价格: ${result.value:,.2f} (来源: {result.provider})")
        print()
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        print()
    
    try:
        # 测试总市值
        print("2. 测试总市值...")
        result = fetcher.get(DataType.TOTAL_MARKET_CAP)
        print(f"   [OK] 总市值: ${result.value:,.0f} (来源: {result.provider})")
        print()
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        print()
    
    try:
        # 测试稳定币市值
        print("3. 测试稳定币市值...")
        result = fetcher.get(DataType.STABLECOIN_MARKET_CAP)
        print(f"   [OK] 稳定币市值: ${result.value:,.0f} (来源: {result.provider})")
        print()
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        print()
    
    try:
        # 测试MA50
        print("4. 测试MA50...")
        result = fetcher.get(DataType.MA50)
        print(f"   [OK] MA50: ${result.value:,.2f} (来源: {result.provider})")
        print()
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        print()
    
    try:
        # 测试MA200
        print("5. 测试MA200...")
        result = fetcher.get(DataType.MA200)
        print(f"   [OK] MA200: ${result.value:,.2f} (来源: {result.provider})")
        print()
    except Exception as e:
        print(f"   [FAIL] 失败: {e}")
        print()
    
    print("=" * 50)
    print("所有测试完成！")
    print("=" * 50)

if __name__ == "__main__":
    test_api()

