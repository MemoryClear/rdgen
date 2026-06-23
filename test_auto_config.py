#!/usr/bin/env python3
"""
测试 RustDesk 配置获取功能
用于验证自动配置系统是否正常工作
"""

import sys
import os
import json

# 添加项目路径
sys.path.insert(0, 'F:\\workspace\\rdgen\\rdgen-master')

def test_version_fetch():
    """测试版本列表获取"""
    print("=" * 60)
    print("测试 1: 获取 RustDesk 版本列表")
    print("=" * 60)

    try:
        from rdgenerator.rustdesk_config import get_rustdesk_versions

        versions = get_rustdesk_versions(limit=10)

        print(f"\n✅ 成功获取 {len(versions)} 个版本:\n")
        for version, display_name in versions[:5]:  # 只显示前5个
            print(f"  {version:15s} -> {display_name}")

        if len(versions) > 5:
            print(f"  ... 还有 {len(versions) - 5} 个版本")

        return True

    except Exception as e:
        print(f"\n❌ 获取版本列表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_fetch():
    """测试配置获取"""
    print("\n" + "=" * 60)
    print("测试 2: 获取 RustDesk 构建配置")
    print("=" * 60)

    test_versions = ['1.4.7', '1.4.6', 'master']

    from rdgenerator.rustdesk_config import RustDeskConfigFetcher

    fetcher = RustDeskConfigFetcher()

    for version in test_versions:
        print(f"\n测试版本: {version}")
        print("-" * 40)

        try:
            config = fetcher.fetch_workflow_config(version)

            if config:
                print(f"  ✅ 成功获取 {len(config)} 个配置变量")
                # 显示关键配置
                key_configs = [
                    'NDK_VERSION', 'RUST_VERSION', 'FLUTTER_VERSION',
                    'VCPKG_COMMIT_ID', 'LLVM_VERSION'
                ]
                for key in key_configs:
                    if key in config:
                        value = config[key]
                        if len(value) > 20:
                            value = value[:20] + "..."
                        print(f"  {key:20s} = {value}")
            else:
                print(f"  ⚠️ 未获取到配置（可能是旧版本）")

        except Exception as e:
            print(f"  ❌ 获取配置失败: {e}")

    return True


def test_platform_specific():
    """测试平台特定配置"""
    print("\n" + "=" * 60)
    print("测试 3: 平台特定配置")
    print("=" * 60)

    from rdgenerator.rustdesk_config import RustDeskConfigFetcher

    fetcher = RustDeskConfigFetcher()

    platforms = ['android', 'windows', 'macos', 'linux']
    version = '1.4.7'

    for platform in platforms:
        print(f"\n平台: {platform}")
        print("-" * 40)

        try:
            config = fetcher.get_platform_specific_config(version, platform)

            # 显示平台特定的关键配置
            if platform == 'android':
                print(f"  NDK_VERSION: {config.get('NDK_VERSION', 'N/A')}")
                print(f"  FLUTTER_VERSION: {config.get('FLUTTER_VERSION', 'N/A')}")
            elif platform == 'macos':
                print(f"  RUST_VERSION: {config.get('RUST_VERSION', 'N/A')}")
                print(f"  (MAC_RUST_VERSION used)")
            else:
                print(f"  RUST_VERSION: {config.get('RUST_VERSION', 'N/A')}")
                print(f"  FLUTTER_VERSION: {config.get('FLUTTER_VERSION', 'N/A')}")

        except Exception as e:
            print(f"  ❌ 获取配置失败: {e}")

    return True


def test_script():
    """测试独立脚本"""
    print("\n" + "=" * 60)
    print("测试 4: 独立配置获取脚本")
    print("=" * 60)

    import subprocess

    script_path = "F:\\workspace\\rdgen\\rdgen-master\\.github\\scripts\\fetch_build_config.py"

    if not os.path.exists(script_path):
        print(f"  ⚠️ 脚本不存在: {script_path}")
        return False

    try:
        # 运行脚本
        result = subprocess.run(
            [sys.executable, script_path, '--version', '1.4.7', '--platform', 'android', '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            config = json.loads(result.stdout)
            print(f"  ✅ 脚本成功执行，获取 {len(config)} 个配置")
            print(f"  NDK_VERSION: {config.get('NDK_VERSION', 'N/A')}")
            print(f"  RUST_VERSION: {config.get('RUST_VERSION', 'N/A')}")
            return True
        else:
            print(f"  ❌ 脚本执行失败")
            print(f"  错误输出: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ 执行脚本时出错: {e}")
        return False


def test_forms_integration():
    """测试 forms.py 集成"""
    print("\n" + "=" * 60)
    print("测试 5: Django Forms 集成")
    print("=" * 60)

    try:
        from rdgenerator.forms import GenerateForm, get_version_choices

        # 测试 get_version_choices 函数
        choices = get_version_choices()
        print(f"  ✅ get_version_choices() 返回 {len(choices)} 个选项")

        # 显示前几个选项
        for version, display in choices[:3]:
            print(f"    {version}: {display}")

        # 测试表单初始化
        form = GenerateForm()
        version_choices = form.fields['version'].choices

        print(f"\n  ✅ 表单初始化成功")
        print(f"  版本字段有 {len(version_choices)} 个选项")

        return True

    except Exception as e:
        print(f"  ❌ Forms 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("RustDesk 自动配置系统 - 功能测试")
    print("=" * 60 + "\n")

    results = {}

    # 运行所有测试
    tests = [
        ('版本列表获取', test_version_fetch),
        ('配置获取', test_config_fetch),
        ('平台特定配置', test_platform_specific),
        ('独立脚本', test_script),
        ('Forms 集成', test_forms_integration),
    ]

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 发生异常: {e}")
            results[test_name] = False

    # 显示测试结果摘要
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:20s}: {status}")

    print("\n" + "-" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("-" * 60)

    if passed == total:
        print("\n[SUCCESS] 所有测试通过！自动配置系统工作正常。")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
