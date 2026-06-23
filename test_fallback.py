#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试兜底配置功能
验证在 GitHub API 失败时能否正确使用兜底配置
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, 'F:\\workspace\\rdgen\\rdgen-master')


def test_fallback_config_file():
    """测试兜底配置文件是否存在且格式正确"""
    print("=" * 60)
    print("测试 1: 兜底配置文件检查")
    print("=" * 60)

    config_file = "F:\\workspace\\rdgen\\rdgen-master\\rdgenerator\\fallback_config.yaml"

    if not os.path.exists(config_file):
        print(f"  [FAIL] 配置文件不存在: {config_file}")
        return False

    print(f"  [OK] 配置文件存在: {config_file}")

    # 检查文件格式
    try:
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查必要的键
        if 'versions' not in config:
            print(f"  [FAIL] 配置文件缺少 'versions' 键")
            return False

        if 'build_configs' not in config:
            print(f"  [FAIL] 配置文件缺少 'build_configs' 键")
            return False

        print(f"  [OK] YAML 格式正确")
        print(f"  [OK] 包含 {len(config['versions'])} 个版本")
        print(f"  [OK] 包含 {len(config['build_configs'])} 个构建配置")

        # 显示部分内容
        print(f"\n  版本列表示例:")
        for v in config['versions'][:3]:
            print(f"    - {v['version']}: {v['display']}")

        return True

    except Exception as e:
        print(f"  [FAIL] 解析配置文件失败: {e}")
        return False


def test_load_fallback_config():
    """测试加载兜底配置"""
    print("\n" + "=" * 60)
    print("测试 2: 加载兜底配置")
    print("=" * 60)

    try:
        # 检查 PyYAML 是否安装
        try:
            import yaml
        except ImportError:
            print("  [SKIP] PyYAML 未安装，跳过此测试")
            print("  提示: pip install PyYAML")
            return True

        from rdgenerator.rustdesk_config import RustDeskConfigFetcher

        config = RustDeskConfigFetcher.load_fallback_config_from_file()

        if config:
            print(f"  [OK] 成功加载兜底配置")
            print(f"  [OK] 配置包含键: {list(config.keys())}")
            return True
        else:
            print(f"  [FAIL] 加载返回 None")
            return False

    except Exception as e:
        print(f"  [FAIL] 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_versions():
    """测试兜底版本列表"""
    print("\n" + "=" * 60)
    print("测试 3: 获取兜底版本列表")
    print("=" * 60)

    try:
        from rdgenerator.rustdesk_config import RustDeskConfigFetcher

        versions = RustDeskConfigFetcher.get_fallback_versions()

        if not versions:
            print(f"  [FAIL] 版本列表为空")
            return False

        print(f"  [OK] 获取到 {len(versions)} 个版本")

        # 显示版本列表
        print(f"\n  版本列表:")
        for version, display in versions[:5]:
            print(f"    {version:15s} -> {display}")

        if len(versions) > 5:
            print(f"    ... 还有 {len(versions) - 5} 个版本")

        return True

    except Exception as e:
        print(f"  [FAIL] 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_build_config():
    """测试兜底构建配置"""
    print("\n" + "=" * 60)
    print("测试 4: 获取兜底构建配置")
    print("=" * 60)

    try:
        from rdgenerator.rustdesk_config import RustDeskConfigFetcher

        # 测试默认配置
        default_config = RustDeskConfigFetcher.get_default_config()

        if not default_config:
            print(f"  [FAIL] 默认配置为空")
            return False

        print(f"  [OK] 获取默认配置，包含 {len(default_config)} 个变量")

        # 显示关键配置
        key_configs = [
            'NDK_VERSION', 'RUST_VERSION', 'FLUTTER_VERSION',
            'VCPKG_COMMIT_ID'
        ]

        print(f"\n  关键配置:")
        for key in key_configs:
            value = default_config.get(key, 'N/A')
            if len(str(value)) > 20:
                value = str(value)[:20] + "..."
            print(f"    {key:20s} = {value}")

        return True

    except Exception as e:
        print(f"  [FAIL] 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_version_specific_config():
    """测试版本特定配置"""
    print("\n" + "=" * 60)
    print("测试 5: 版本特定配置")
    print("=" * 60)

    try:
        from rdgenerator.rustdesk_config import RustDeskConfigFetcher

        # 测试已知版本
        test_versions = ['1.4.7', '1.4.6']

        for version in test_versions:
            config = RustDeskConfigFetcher.get_version_specific_fallback_config(version)

            if config:
                print(f"  [OK] 版本 {version} 有特定配置")
                if 'NDK_VERSION' in config:
                    print(f"       NDK_VERSION: {config['NDK_VERSION']}")
            else:
                print(f"  [INFO] 版本 {version} 使用默认配置")

        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forms_integration():
    """测试 forms.py 集成"""
    print("\n" + "=" * 60)
    print("测试 6: forms.py 兜底集成")
    print("=" * 60)

    try:
        # 测试 get_version_choices 函数
        from rdgenerator.forms import get_version_choices

        versions = get_version_choices()

        if not versions:
            print(f"  [FAIL] 返回空列表")
            return False

        print(f"  [OK] get_version_choices() 返回 {len(versions)} 个版本")

        # 显示部分版本
        print(f"\n  版本列表:")
        for version, display in versions[:3]:
            print(f"    {version}: {display}")

        return True

    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("兜底配置功能测试")
    print("=" * 60 + "\n")

    results = {}

    # 运行所有测试
    tests = [
        ('配置文件检查', test_fallback_config_file),
        ('加载兜底配置', test_load_fallback_config),
        ('兜底版本列表', test_fallback_versions),
        ('兜底构建配置', test_fallback_build_config),
        ('版本特定配置', test_version_specific_config),
        ('Forms 集成', test_forms_integration),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n[FAIL] 测试 '{test_name}' 发生异常: {e}")
            results[test_name] = False

    # 显示测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name:20s}: {status}")

    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("-" * 60)

    if passed == total:
        print("\n[SUCCESS] 兜底配置功能正常！")
        print("\n功能说明:")
        print("  1. 当 GitHub API 失败时，自动使用 fallback_config.yaml")
        print("  2. 支持版本特定的构建配置")
        print("  3. 多层兜底机制确保可用性")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
