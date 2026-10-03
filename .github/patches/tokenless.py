#!/usr/bin/env python3
"""
tokenless.py — 阻止 API 的 access_token 进入远程连接流程。

## 修的是什么

报错: `Failed to secure tcp: deadline has elapsed: Please try later`

`src/client.rs::_start_inner` 里:

    let legacy_secure = !key.is_empty() && (!token.is_empty() || !switch_code.is_empty());
    ...
    if !exchanged && legacy_secure {
        secure_tcp(&mut socket, &key).await
            .map_err(|e| anyhow!("Failed to secure tcp: {}", e))?;
    }

* `key` = `crate::get_key()` —— 为空会回落到编译期常量 `RS_PUB_KEY`
  (rdgen 已把它换成自建服务器的公钥), 所以**永远非空**;
* `token` = `LocalConfig::get_option("access_token")` —— 只要在客户端里
  **登录过自建 API 服务器**(lejianwen/rustdesk-api 之类)就会被写入。

两者同时非空 => 客户端会对 hbbs 强制发起 secure_tcp 加密握手。而 `secure_tcp` ->
`key_exchange()` 只是**被动等待 hbbs 主动推送 KeyExchange**, 开源 hbbs 在这个场景
不会推送, 客户端读超时 -> tokio 的 `Elapsed` 显示为 `deadline has elapsed`。

因为这条 TCP 是"连任何对端之前"的必经步骤(与对端无关), 所以症状是
**连任何机器都失败**; 而客户端自己注册走 UDP, 不做该握手, 所以 App 看着在线。

## 本补丁做什么

保留 API 登录、账号信息、设备列表、地址簿、文件传输等**全部功能**,
只把 token 从连接流程里摘掉:

    src/ui_session_interface.rs:
        let token = LocalConfig::get_option("access_token");
    ->  let token = String::new();

该变量在 `io_loop` 中**只**用于连接(端口转发 + `Remote::io_loop` -> `Client::start`),
所以一行即可覆盖 Android / 桌面 / Flutter / CLI / port-forward 全部路径。

不影响客户端之间(peer <-> peer)的端到端加密 —— 那条走 `src/client.rs::secure_connection`,
用的是对端公钥, 与本补丁无关。

另一处 `LocalConfig::get_option("access_token")`
(`ui_session_interface.rs::get_audit_server`, 判断是否为空) **保持原样**。

## 行为约定

* 幂等: 已打过则跳过;
* 锚点找不到 -> `exit 1`(宁可构建失败, 也不要再出现静默失效的补丁)。
"""

import os
import re
import sys

TARGET = "src/ui_session_interface.rs"
ANCHOR_RE = re.compile(r'^(\s*)let token = LocalConfig::get_option\("access_token"\);')
PATCHED_RE = re.compile(r'^\s*let token = String::new\(\);\s*$')
MARKER = "rdgen: tokenless"


def main() -> int:
    if not os.path.exists(TARGET):
        print(f"ERROR: {TARGET} not found (run this from the rustdesk checkout root)", file=sys.stderr)
        return 1

    with open(TARGET, "r", encoding="utf-8", newline="") as f:
        lines = f.readlines()

    new_lines = []
    hits = 0
    for line in lines:
        m = ANCHOR_RE.match(line)
        if not m:
            new_lines.append(line)
            continue
        hits += 1
        indent = m.group(1)
        eol = "\r\n" if line.endswith("\r\n") else "\n"
        new_lines.append(f"{indent}// {MARKER} — keep API login, but never feed access_token" + eol)
        new_lines.append(f"{indent}// into the connection path. Otherwise src/client.rs forces a secure_tcp" + eol)
        new_lines.append(f"{indent}// handshake to hbbs and a self-hosted hbbs never answers:" + eol)
        new_lines.append(f'{indent}// "Failed to secure tcp: deadline has elapsed" on every connect.' + eol)
        new_lines.append(f"{indent}let token = String::new();" + eol)

    if hits == 0:
        for line in lines:
            if PATCHED_RE.match(line):
                print(f"{TARGET}: already patched, skipping")
                return 0
        print(
            f"ERROR: anchor not found in {TARGET}:\n"
            '       let token = LocalConfig::get_option("access_token");\n'
            "       upstream may have refactored the connection token path — "
            "update tokenless.py (do NOT let it pass silently)",
            file=sys.stderr,
        )
        return 1

    with open(TARGET, "w", encoding="utf-8", newline="") as f:
        f.writelines(new_lines)

    print(f"{TARGET}: patched {hits} site(s) — connection token is now always empty (tokenless)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
