# sub-proxy

订阅链接 UA 转发代理 — 将代理客户端的订阅请求转发到上游，并注入自定义 `User-Agent`。

## 动机

一些代理管理工具（如 daed）在拉取订阅链接时无法自定义 `User-Agent`，而部分订阅服务会通过 UA 限制访问。本工具作为中间代理，在转发时替换 UA，从而绕过此类限制。

## 使用方法

```bash
# 测试模式（使用 httpbin.org 验证 UA 是否生效）
python3 sub_proxy.py

# 指定上游和 UA
python3 sub_proxy.py \
  --upstream "https://example.com/sub/token" \
  --ua "clash-verge/v2.5.3"

# 自签名证书时跳过 SSL 验证
python3 sub_proxy.py \
  --upstream "https://example.com/sub/token" \
  --no-verify-ssl
```

### 参数

| 参数 | 简写 | 环境变量 | 默认值 |
|------|------|----------|--------|
| `--port` | `-p` | `PROXY_PORT` | `25500` |
| `--upstream` | `-u` | `UPSTREAM_URL` | `httpbin.org/headers`（测试） |
| `--ua` | `-a` | `CUSTOM_UA` | `clash-verge/v2.5.3` |
| `--no-verify-ssl` | | | 关闭 SSL 验证 |

### daed 中配置

在 daed 中将订阅地址设为：

```
http://127.0.0.1:25500/
```

## Docker

### docker-compose

```yaml
services:
  sub-proxy:
    image: ghcr.io/fffold/sub-proxy
    container_name: sub-proxy
    restart: unless-stopped
    ports:
      - "25500:25500"
    environment:
      - UPSTREAM_URL=https://example.com/sub/token
      - CUSTOM_UA=v2rayN/7.24.4
      - LOG_LEVEL=INFO
```

### 直接运行

```bash
docker run -d \
  --name sub-proxy \
  -p 25500:25500 \
  -e UPSTREAM_URL=https://example.com/sub/token \
  -e CUSTOM_UA=v2rayN/7.24.4 \
  ghcr.io/fffold/sub-proxy
```

## 许可证

MIT
