#!/usr/bin/env python3
"""
RustDesk 构建配置获取脚本
用于 GitHub Actions 工作流中，从 RustDesk 官方仓库获取构建配置

使用方法:
    python fetch_build_config.py --version 1.4.7 --platform windows --output env
    python fetch_build_config.py --version master --platform android --output json
"""

import argparse
import json
import sys
import os
import re
import base64
import requests
from typing import Dict, Optional


class RustDeskConfigFetcher:
    """RustDesk 官方配置获取器"""

    GITHUB_API_BASE = "https://api.github.com"
    RUSTDESK_REPO = "rustdesk/rustdesk"
    WORKFLOW_FILE = ".github/workflows/flutter-build.yml"
    BRIDGE_WORKFLOW_FILE = ".github/workflows/bridge.yml"

    def __init__(self, github_token: Optional[str] = None):
        """
        初始化配置获取器

        Args:
            github_token: GitHub API Token（可选，用于提高请求限制）
        """
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')

    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'RDGen-BuildConfigFetcher/1.0'
        }
        if self.github_token:
            headers['Authorization'] = f'Bearer {self.github_token}'
        return headers

    def fetch_workflow_file(self, file_path: str, ref: str) -> Optional[str]:
        """
        获取指定的 workflow 文件内容

        Args:
            file_path: 文件路径
            ref: Git 引用（分支或标签）

        Returns:
            文件内容或 None
        """
        try:
            url = f"{self.GITHUB_API_BASE}/repos/{self.RUSTDESK_REPO}/contents/{file_path}"
            params = {'ref': ref}

            response = requests.get(
                url,
                headers=self.get_headers(),
                params=params,
                timeout=15
            )

            if response.status_code == 404:
                print(f"Warning: Workflow file not found: {file_path} at ref {ref}", file=sys.stderr)
                return None

            response.raise_for_status()

            content = response.json()
            file_content = base64.b64decode(content['content']).decode('utf-8')

            return file_content

        except Exception as e:
            print(f"Error fetching workflow file {file_path}: {e}", file=sys.stderr)
            return None

    def parse_workflow_env(self, yaml_content: str) -> Dict[str, str]:
        """
        解析 workflow YAML 文件中的 env 变量

        Args:
            yaml_content: YAML 文件内容

        Returns:
            配置字典
        """
        config = {}

        # 使用正则表达式提取 env 部分的变量
        env_pattern = re.compile(
            r'^\s{2}([A-Z_]+):\s*["\']?([^"\':\n]+)["\']?',
            re.MULTILINE
        )

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

    def fetch_config(self, version: str) -> Dict[str, str]:
        """
        从 RustDesk 官方仓库获取指定版本的构建配置

        Args:
            version: RustDesk 版本号或 'master'

        Returns:
            配置字典
        """
        # 确定分支/标签
        ref = 'master' if version == 'master' else f'refs/tags/{version}'

        config = {}

        # 获取 flutter-build.yml
        print(f"Fetching {self.WORKFLOW_FILE} for version {version}...", file=sys.stderr)
        flutter_build_content = self.fetch_workflow_file(self.WORKFLOW_FILE, ref)
        if flutter_build_content:
            flutter_config = self.parse_workflow_env(flutter_build_content)
            config.update(flutter_config)
            print(f"  Found {len(flutter_config)} variables in flutter-build.yml", file=sys.stderr)

        # 获取 bridge.yml (可能使用不同的 Flutter 版本)
        print(f"Fetching {self.BRIDGE_WORKFLOW_FILE}...", file=sys.stderr)
        bridge_content = self.fetch_workflow_file(self.BRIDGE_WORKFLOW_FILE, ref)
        if bridge_content:
            bridge_config = self.parse_workflow_env(bridge_content)
            # Bridge 使用不同的前缀存储
            for key, value in bridge_config.items():
                if key.startswith('FLUTTER_'):
                    config[f'BRIDGE_{key}'] = value
                else:
                    config[key] = value
            print(f"  Found {len(bridge_config)} variables in bridge.yml", file=sys.stderr)

        return config

    def get_platform_config(self, version: str, platform: str) -> Dict[str, str]:
        """
        获取平台特定的配置

        Args:
            version: RustDesk 版本
            platform: 平台名称

        Returns:
            配置字典
        """
        base_config = self.fetch_config(version)

        # 平台特定的调整
        if platform == 'android':
            # Android 使用 ANDROID_FLUTTER_VERSION
            if 'ANDROID_FLUTTER_VERSION' in base_config:
                base_config['FLUTTER_VERSION'] = base_config['ANDROID_FLUTTER_VERSION']

        elif platform == 'macos':
            # macOS 使用 MAC_RUST_VERSION
            if 'MAC_RUST_VERSION' in base_config:
                base_config['RUST_VERSION'] = base_config['MAC_RUST_VERSION']

        elif platform in ['windows', 'windows-x86']:
            # Windows 可能需要的特定配置
            pass

        return base_config


def output_as_env(config: Dict[str, str], prefix: str = "RDDESK_"):
    """
    以 GitHub Actions 环境变量格式输出配置

    Args:
        config: 配置字典
        prefix: 环境变量前缀
    """
    # 输出到 GITHUB_ENV 文件（如果存在）
    github_env = os.environ.get('GITHUB_ENV')

    output_lines = []
    for key, value in sorted(config.items()):
        env_name = f"{prefix}{key}"
        line = f"{env_name}={value}"
        print(line)  # 打印到 stdout
        output_lines.append(line)

    if github_env:
        with open(github_env, 'a') as f:
            f.write('\n'.join(output_lines) + '\n')
        print(f"\nWritten {len(output_lines)} variables to GITHUB_ENV", file=sys.stderr)


def output_as_json(config: Dict[str, str]):
    """
    以 JSON 格式输出配置

    Args:
        config: 配置字典
    """
    print(json.dumps(config, indent=2, sort_keys=True))


def output_as_yaml(config: Dict[str, str]):
    """
    以 YAML 格式输出配置

    Args:
        config: 配置字典
    """
    print("# RustDesk Build Configuration")
    print("# Auto-fetched from official repository")
    print()
    for key, value in sorted(config.items()):
        # 如果值包含特殊字符，使用引号
        if any(c in value for c in [':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
            print(f"{key}: \"{value}\"")
        else:
            print(f"{key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch RustDesk build configuration from official repository'
    )
    parser.add_argument(
        '--version',
        required=True,
        help='RustDesk version (e.g., 1.4.7, master)'
    )
    parser.add_argument(
        '--platform',
        default='windows',
        choices=['windows', 'windows-x86', 'android', 'linux', 'macos'],
        help='Target platform'
    )
    parser.add_argument(
        '--output',
        default='env',
        choices=['env', 'json', 'yaml'],
        help='Output format (env: GitHub Actions env vars, json: JSON, yaml: YAML)'
    )
    parser.add_argument(
        '--prefix',
        default='RDDESK_',
        help='Environment variable prefix (only for env output)'
    )
    parser.add_argument(
        '--github-token',
        help='GitHub API token (optional, increases rate limit)'
    )

    args = parser.parse_args()

    # 创建配置获取器
    fetcher = RustDeskConfigFetcher(github_token=args.github_token)

    # 获取配置
    print(f"Fetching RustDesk build config for version={args.version}, platform={args.platform}", file=sys.stderr)

    try:
        config = fetcher.get_platform_config(args.version, args.platform)

        if not config:
            print("Error: No configuration found", file=sys.stderr)
            sys.exit(1)

        print(f"Successfully fetched {len(config)} configuration variables", file=sys.stderr)
        print(file=sys.stderr)

        # 输出配置
        if args.output == 'env':
            output_as_env(config, args.prefix)
        elif args.output == 'json':
            output_as_json(config)
        elif args.output == 'yaml':
            output_as_yaml(config)

    except Exception as e:
        print(f"Error: Failed to fetch configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
