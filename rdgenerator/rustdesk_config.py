"""
RustDesk 官方配置获取工具
用于从 RustDesk GitHub 仓库获取构建配置
"""
import requests
import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RustDeskConfigFetcher:
    """RustDesk 官方配置获取器"""

    GITHUB_API_BASE = "https://api.github.com"
    RUSTDESK_REPO = "rustdesk/rustdesk"
    WORKFLOW_FILE = ".github/workflows/flutter-build.yml"
    BRIDGE_WORKFLOW_FILE = ".github/workflows/bridge.yml"

    # 缓存配置
    CACHE_PREFIX = "rustdesk_config_"
    CACHE_TIMEOUT = 3600  # 1小时缓存

    @staticmethod
    def get_github_headers() -> Dict[str, str]:
        """获取 GitHub API 请求头"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'RDGen-ConfigFetcher/1.0'
        }
        # 如果有 GitHub Token，添加到请求头
        from django.conf import settings
        if hasattr(settings, 'GHBEARER') and settings.GHBEARER:
            headers['Authorization'] = f'Bearer {settings.GHBEARER}'
        return headers

    @classmethod
    def fetch_releases(cls, limit: int = 50) -> List[Tuple[str, str]]:
        """
        从 GitHub Releases 获取 RustDesk 版本列表

        Args:
            limit: 最大获取数量

        Returns:
            版本列表 [(version, display_name), ...]
        """
        cache_key = f"{cls.CACHE_PREFIX}releases_{limit}"

        # 尝试从缓存获取
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            url = f"{cls.GITHUB_API_BASE}/repos/{cls.RUSTDESK_REPO}/releases"
            params = {'per_page': limit}

            response = requests.get(
                url,
                headers=cls.get_github_headers(),
                params=params,
                timeout=10
            )
            response.raise_for_status()

            releases = response.json()
            versions = []

            # 添加 master/nightly 选项
            versions.append(('master', 'nightly (master - development build)'))

            # 处理发布版本
            for release in releases:
                tag_name = release.get('tag_name', '')
                if tag_name:
                    # tag_name 通常是 "1.4.7" 格式
                    display_name = f"{tag_name}"
                    if release.get('prerelease'):
                        display_name += " (pre-release)"
                    versions.append((tag_name, display_name))

            # 缓存结果
            cache.set(cache_key, versions, cls.CACHE_TIMEOUT)

            logger.info(f"Fetched {len(versions)} RustDesk releases from GitHub")
            return versions

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch RustDesk releases: {e}")
            # 返回已知的稳定版本作为后备
            return cls.get_fallback_versions()

    @classmethod
    def get_fallback_versions(cls) -> List[Tuple[str, str]]:
        """
        获取后备版本列表（当 GitHub API 不可用时）

        Returns:
            版本列表
        """
        return [
            ('master', 'nightly (master - development build)'),
            ('1.4.7', '1.4.7'),
            ('1.4.6', '1.4.6'),
            ('1.4.5', '1.4.5'),
            ('1.4.4', '1.4.4'),
            ('1.4.3', '1.4.3'),
            ('1.4.2', '1.4.2'),
            ('1.4.1', '1.4.1'),
            ('1.4.0', '1.4.0'),
            ('1.3.9', '1.3.9'),
        ]

    @classmethod
    def fetch_workflow_config(cls, version: str) -> Dict[str, str]:
        """
        从 RustDesk 官方仓库获取指定版本的 workflow 配置

        Args:
            version: RustDesk 版本号或 'master'

        Returns:
            配置字典 {变量名: 值}
        """
        cache_key = f"{cls.CACHE_PREFIX}workflow_{version}"

        # 尝试从缓存获取
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Using cached config for version {version}")
            return cached

        try:
            # 确定分支/标签
            ref = 'master' if version == 'master' else f'refs/tags/{version}'

            # 获取主构建配置文件
            config = {}

            # 获取 flutter-build.yml
            flutter_build_config = cls.fetch_workflow_file(
                cls.WORKFLOW_FILE,
                ref,
                'flutter-build'
            )
            if flutter_build_config:
                config.update(flutter_build_config)

            # 获取 bridge.yml (可能使用不同的 Flutter 版本)
            bridge_config = cls.fetch_workflow_file(
                cls.BRIDGE_WORKFLOW_FILE,
                ref,
                'bridge'
            )
            if bridge_config:
                # Bridge 使用不同的前缀存储
                for key, value in bridge_config.items():
                    if key.startswith('FLUTTER_'):
                        config[f'BRIDGE_{key}'] = value
                    else:
                        config[key] = value

            # 缓存结果
            if config:
                cache.set(cache_key, config, cls.CACHE_TIMEOUT)
                logger.info(f"Fetched and cached config for version {version}")

            return config

        except Exception as e:
            logger.error(f"Failed to fetch workflow config for {version}: {e}")
            # 返回默认配置
            return cls.get_default_config()

    @classmethod
    def fetch_workflow_file(cls, file_path: str, ref: str, config_type: str) -> Optional[Dict[str, str]]:
        """
        获取指定的 workflow 文件并解析配置

        Args:
            file_path: 文件路径
            ref: Git 引用（分支或标签）
            config_type: 配置类型标识

        Returns:
            配置字典或 None
        """
        try:
            # 使用 GitHub API 获取文件内容
            url = f"{cls.GITHUB_API_BASE}/repos/{cls.RUSTDESK_REPO}/contents/{file_path}"
            params = {'ref': ref}

            response = requests.get(
                url,
                headers=cls.get_github_headers(),
                params=params,
                timeout=15
            )

            if response.status_code == 404:
                logger.warning(f"Workflow file not found: {file_path} at ref {ref}")
                return None

            response.raise_for_status()

            # GitHub API 返回 base64 编码的内容
            import base64
            content = response.json()
            file_content = base64.b64decode(content['content']).decode('utf-8')

            # 解析 YAML 文件中的 env 变量
            config = cls.parse_workflow_env(file_content)

            logger.info(f"Parsed {len(config)} variables from {file_path}")
            return config

        except Exception as e:
            logger.error(f"Error fetching workflow file {file_path}: {e}")
            return None

    @staticmethod
    def parse_workflow_env(yaml_content: str) -> Dict[str, str]:
        """
        解析 workflow YAML 文件中的 env 变量

        Args:
            yaml_content: YAML 文件内容

        Returns:
            配置字典
        """
        config = {}

        # 使用正则表达式提取 env 部分的变量
        # 匹配格式: VAR_NAME: "value" 或 VAR_NAME: value
        env_pattern = re.compile(
            r'^\s{2}([A-Z_]+):\s*["\']?([^"\':\n]+)["\']?',
            re.MULTILINE
        )

        # 我们只关心 env: 之后的部分
        lines = yaml_content.split('\n')
        in_env_section = False

        for line in lines:
            # 检测 env: 行
            if re.match(r'^env:', line):
                in_env_section = True
                continue

            # 检测下一个顶级部分（非缩进的行），退出 env
            if in_env_section and line and not line[0].isspace():
                break

            # 在 env 部分内，解析变量
            if in_env_section:
                match = env_pattern.match(line)
                if match:
                    var_name = match.group(1)
                    var_value = match.group(2).strip()

                    # 跳过动态变量（包含 ${{ }}）
                    if '${{' not in var_value:
                        # 清理值（移除注释）
                        if '#' in var_value:
                            var_value = var_value.split('#')[0].strip()

                        config[var_name] = var_value

        return config

    @classmethod
    def get_default_config(cls) -> Dict[str, str]:
        """
        获取默认配置（当无法获取官方配置时使用）

        Returns:
            默认配置字典
        """
        return {
            'SCITER_RUST_VERSION': '1.75',
            'RUST_VERSION': '1.75',
            'MAC_RUST_VERSION': '1.81',
            'CARGO_NDK_VERSION': '3.1.2',
            'SCITER_ARMV7_CMAKE_VERSION': '3.29.7',
            'SCITER_NASM_DEBVERSION': '2.15.05-1',
            'LLVM_VERSION': '15.0.6',
            'FLUTTER_VERSION': '3.24.5',
            'ANDROID_FLUTTER_VERSION': '3.24.5',
            'FLUTTER_ELINUX_VERSION': '3.16.9',
            'VCPKG_COMMIT_ID': '120deac3062162151622ca4860575a33844ba10b',
            'ARMV7_VCPKG_COMMIT_ID': '6f29f12e82a8293156836ad81cc9bf5af41fe836',
            'NDK_VERSION': 'r28c',
            # Bridge 专用（可能不同）
            'BRIDGE_FLUTTER_VERSION': '3.22.3',
            'FLUTTER_RUST_BRIDGE_VERSION': '1.80.1',
            'CARGO_EXPAND_VERSION': '1.0.95',
        }

    @classmethod
    def get_platform_specific_config(cls, version: str, platform: str) -> Dict[str, str]:
        """
        获取平台特定的配置

        Args:
            version: RustDesk 版本
            platform: 平台名称 (windows, android, linux, macos)

        Returns:
            平台特定配置字典
        """
        # 获取基础配置
        base_config = cls.fetch_workflow_config(version)

        # 平台特定的调整
        platform_config = {}

        if platform == 'android':
            # Android 使用 ANDROID_FLUTTER_VERSION
            platform_config['FLUTTER_VERSION'] = base_config.get(
                'ANDROID_FLUTTER_VERSION',
                base_config.get('FLUTTER_VERSION', '3.24.5')
            )

        elif platform == 'linux':
            # Linux 可能有特定的依赖
            pass

        elif platform == 'macos':
            # macOS 使用 MAC_RUST_VERSION
            platform_config['RUST_VERSION'] = base_config.get(
                'MAC_RUST_VERSION',
                base_config.get('RUST_VERSION', '1.75')
            )

        elif platform in ['windows', 'windows-x86']:
            # Windows 可能有特定的 NASM 版本
            pass

        # 合并配置
        config = {**base_config, **platform_config}

        return config


def get_rustdesk_versions(limit: int = 50) -> List[Tuple[str, str]]:
    """
    获取 RustDesk 版本列表（便捷函数）

    Args:
        limit: 最大获取数量

    Returns:
        版本列表
    """
    return RustDeskConfigFetcher.fetch_releases(limit)


def get_rustdesk_build_config(version: str, platform: str = 'windows') -> Dict[str, str]:
    """
    获取 RustDesk 构建配置（便捷函数）

    Args:
        version: RustDesk 版本
        platform: 平台名称

    Returns:
        配置字典
    """
    return RustDeskConfigFetcher.get_platform_specific_config(version, platform)
