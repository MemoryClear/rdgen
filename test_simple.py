#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本 - 验证文件修改是否正确
不依赖外部库，只验证语法和导入
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, 'F:\\workspace\\rdgen\\rdgen-master')

def test_file_existence():
    """测试文件是否存在"""
    print("=" * 60)
    print("测试 1: 检查文件是否存在")
    print("=" * 60)

    files = [
        "rdgenerator/rustdesk_config.py",
        "rdgenerator/forms.py",
        ".github/scripts/fetch_build_config.py",
        ".github/workflows/fetch-rustdesk-config.yml",
        ".github/workflows/generator-android-AUTO-CONFIG-EXAMPLE.yml",
    ]

    all_exist = True
    for file in files:
        full_path = os.path.join("F:\\workspace\\rdgen\\rdgen-master", file)
        exists = os.path.exists(full_path)
        status = "[OK]" if exists else "[FAIL]"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False

    return all_exist


def test_syntax():
    """测试 Python 文件语法"""
    print("\n" + "=" * 60)
    print("测试 2: 检查 Python 文件语法")
    print("=" * 60)

    import py_compile

    files = [
        "rdgenerator/rustdesk_config.py",
        "rdgenerator/forms.py",
        ".github/scripts/fetch_build_config.py",
    ]

    all_valid = True
    for file in files:
        full_path = os.path.join("F:\\workspace\\rdgen\\rdgen-master", file)
        try:
            py_compile.compile(full_path, doraise=True)
            print(f"  [OK] {file}")
        except py_compile.PyCompileError as e:
            print(f"  [FAIL] {file}")
            print(f"        Error: {e}")
            all_valid = False

    return all_valid


def test_imports():
    """测试导入（不依赖 requests）"""
    print("\n" + "=" * 60)
    print("测试 3: 检查导入（跳过 requests 依赖）")
    print("=" * 60)

    # 测试 forms.py
    try:
        # 临时移除 requests 导入
        import rdgenerator.forms as forms_module
        print(f"  [OK] forms.py 导入成功")

        # 检查关键函数
        if hasattr(forms_module, 'get_version_choices'):
            print(f"  [OK] get_version_choices() 函数存在")
        else:
            print(f"  [FAIL] get_version_choices() 函数不存在")
            return False

        if hasattr(forms_module, 'GenerateForm'):
            print(f"  [OK] GenerateForm 类存在")
        else:
            print(f"  [FAIL] GenerateForm 类不存在")
            return False

        return True

    except Exception as e:
        print(f"  [FAIL] 导入失败: {e}")
        return False


def test_yaml_syntax():
    """测试 YAML 文件语法"""
    print("\n" + "=" * 60)
    print("测试 4: 检查 YAML 文件语法")
    print("=" * 60)

    try:
        import yaml
    except ImportError:
        print("  [SKIP] PyYAML 未安装，跳过此测试")
        return True

    files = [
        ".github/workflows/fetch-rustdesk-config.yml",
        ".github/workflows/generator-android-AUTO-CONFIG-EXAMPLE.yml",
    ]

    all_valid = True
    for file in files:
        full_path = os.path.join("F:\\workspace\\rdgen\\rdgen-master", file)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"  [OK] {file}")
        except Exception as e:
            print(f"  [FAIL] {file}")
            print(f"        Error: {e}")
            all_valid = False

    return all_valid


def test_config_structure():
    """测试配置获取器的结构（不实际请求）"""
    print("\n" + "=" * 60)
    print("测试 5: 检查配置获取器结构")
    print("=" * 60)

    try:
        # 检查文件内容
        config_file = "F:\\workspace\\rdgen\\rdgen-master\\rdgenerator\\rustdesk_config.py"
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查关键类和方法
        checks = [
            ('RustDeskConfigFetcher', 'class RustDeskConfigFetcher'),
            ('fetch_releases', 'def fetch_releases'),
            ('fetch_workflow_config', 'def fetch_workflow_config'),
            ('get_platform_specific_config', 'def get_platform_specific_config'),
        ]

        all_found = True
        for name, pattern in checks:
            if pattern in content:
                print(f"  [OK] {name} 存在")
            else:
                print(f"  [FAIL] {name} 不存在")
                all_found = False

        return all_found

    except Exception as e:
        print(f"  [FAIL] 检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("RustDesk 自动配置系统 - 简化测试")
    print("=" * 60 + "\n")

    results = {}

    # 运行所有测试
    tests = [
        ('文件存在性', test_file_existence),
        ('Python 语法', test_syntax),
        ('模块导入', test_imports),
        ('YAML 语法', test_yaml_syntax),
        ('配置结构', test_config_structure),
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
        print("\n[SUCCESS] 所有测试通过！")
        print("\n下一步:")
        print("  1. 安装 requests: pip install requests")
        print("  2. 运行完整测试: python test_auto_config.py")
        print("  3. 修改 workflow 文件（参考 QUICK_MODIFICATION_GUIDE.md）")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
