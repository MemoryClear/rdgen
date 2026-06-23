#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试 - 验证兜底配置文件
不依赖 requests 或 django
"""

import sys
import os

print("=" * 60)
print("兜底配置文件验证")
print("=" * 60 + "\n")

config_file = "F:\\workspace\\rdgen\\rdgen-master\\rdgenerator\\fallback_config.yaml"

# 检查文件是否存在
if not os.path.exists(config_file):
    print(f"[FAIL] 配置文件不存在: {config_file}")
    sys.exit(1)

print(f"[OK] 配置文件存在: {config_file}")

# 读取文件内容
with open(config_file, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[OK] 文件大小: {len(content)} 字节\n")

# 检查 YAML 格式（使用简单的文本检查）
checks = [
    ('versions:', '版本列表'),
    ('build_configs:', '构建配置'),
    ('default:', '默认配置'),
    ('platform_specific:', '平台配置'),
]

print("配置文件结构检查:")
for pattern, name in checks:
    if pattern in content:
        print(f"  [OK] 包含 {name}")
    else:
        print(f"  [FAIL] 缺少 {name}")

# 统计版本数量
version_count = content.count('- version:')
print(f"\n[OK] 包含 {version_count} 个版本")

# 检查关键配置
key_configs = [
    'NDK_VERSION',
    'RUST_VERSION',
    'FLUTTER_VERSION',
    'VCPKG_COMMIT_ID',
]

print("\n关键配置检查:")
for config in key_configs:
    if config in content:
        print(f"  [OK] {config}")
    else:
        print(f"  [FAIL] {config}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)

print("\n兜底配置文件结构:")
print("  1. versions - 版本列表（包含 master 和稳定版本）")
print("  2. build_configs:")
print("     - default: 默认构建配置")
print("     - version_specific: 版本特定配置")
print("     - platform_specific: 平台特定配置")
print("  3. metadata: 元数据信息")

print("\n使用场景:")
print("  - GitHub API 不可用时")
print("  - 网络连接失败时")
print("  - 配置获取超时时")
print("  - 自动降级到本地配置")

print("\n" + "=" * 60)
