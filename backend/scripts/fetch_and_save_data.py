#!/usr/bin/env python3
"""脚本：获取市场数据并保存为JSON文件，供前端使用"""

import json
import os
import sys
from pathlib import Path

# 添加父目录到路径，以便导入后端模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from bullbear_backend.data import DataFetcher, DataType
from bullbear_backend.state_machine import StateMachineEngine

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / '.env')

def fetch_and_save_data():
    """获取所有数据并保存为JSON文件"""
    
    # 确保输出目录存在
    output_dir = Path(__file__).parent.parent.parent / 'frontend' / 'public' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("开始获取市场数据...")
    
    try:
        # 获取所有数据
        fetcher = DataFetcher()
        all_data = fetcher.get_all()
        
        # 转换为字典格式
        data_dict = {}
        first_timestamp = None
        for data_type, result in all_data.items():
            data_dict[data_type.value] = result.to_dict()
            # 获取第一个结果的时间戳
            if first_timestamp is None and hasattr(result, 'timestamp'):
                first_timestamp = result.timestamp
        
        # 保存所有数据
        all_data_file = output_dir / 'all_data.json'
        with open(all_data_file, 'w', encoding='utf-8') as f:
            json.dump({
                "ok": True,
                "data": data_dict,
                "timestamp": first_timestamp
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存所有数据到 {all_data_file}")
        
        # 获取市场状态
        engine = StateMachineEngine()
        state_result = engine.evaluate()
        
        # 保存状态数据
        state_file = output_dir / 'state.json'
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                "ok": True,
                **state_result.to_dict()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 已保存状态数据到 {state_file}")
        
        # 保存各个单独的数据类型（可选，用于兼容性）
        for data_type, result in all_data.items():
            single_file = output_dir / f'{data_type.value}.json'
            with open(single_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "ok": True,
                    **result.to_dict()
                }, f, indent=2, ensure_ascii=False)
        
        print("✅ 所有数据获取并保存成功！")
        return True
        
    except Exception as e:
        print(f"❌ 获取数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fetch_and_save_data()
    sys.exit(0 if success else 1)

