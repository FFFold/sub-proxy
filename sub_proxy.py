#!/usr/bin/env python3
"""
订阅链接 UA 转发代理
将 daed 的订阅请求转发到上游订阅链接，并添加自定义 User-Agent。

用法:
  python3 sub_proxy.py [--port PORT] [--upstream URL] [--ua UA]

示例:
  # 测试模式（默认用 httpbin.org 验证 UA）
  python3 sub_proxy.py

  # 使用真实订阅链接
  python3 sub_proxy.py --upstream "https://example.com/sub/token" --ua "clash-verge/v2.5.3"
"""

import sys
import os
import argparse
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

import requests

# 默认值
DEFAULT_PORT = 25500
DEFAULT_UA = "clash-verge/v2.5.3"
# 测试用的上游，会回显请求头，方便验证 UA 是否正确设置
TEST_UPSTREAM = "https://httpbin.org/headers"


class ProxyHandler(BaseHTTPRequestHandler):
    """处理订阅请求并转发到上游"""

    upstream_url = ""
    custom_ua = ""
    verify_ssl = True

    def do_GET(self):
        logging.info(f"← 收到请求: {self.path}")

        path = self.path.lstrip("/")
        if path.startswith("http://") or path.startswith("https://"):
            upstream_url = path.split("#")[0]
            logging.info(f"  从路径提取上游: {upstream_url}")
        else:
            upstream_url = self.upstream_url

        headers = {k: v for k, v in self.headers.items()}
        headers["User-Agent"] = self.custom_ua

        parsed = urlparse(upstream_url)
        headers["Host"] = parsed.netloc

        try:
            logging.info(f"→ 转发至: {upstream_url}")
            logging.info(f"   User-Agent: {self.custom_ua}")

            resp = requests.get(
                upstream_url,
                headers=headers,
                timeout=60,
                verify=self.verify_ssl,
            )

            logging.info(f"← 上游响应: {resp.status_code} ({len(resp.content)} bytes)")

            self.send_response(resp.status_code)

            hop_by_hop = {
                "connection", "transfer-encoding", "keep-alive",
                "proxy-authenticate", "proxy-authorization",
                "te", "trailers", "upgrade",
            }
            for k, v in resp.headers.items():
                if k.lower() not in hop_by_hop:
                    self.send_header(k, v)

            self.end_headers()
            self.wfile.write(resp.content)

        except requests.exceptions.SSLError as e:
            logging.error(f"SSL 错误: {e}")
            self.send_error(502, f"SSL Error: {e}")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"连接错误: {e}")
            self.send_error(502, f"Connection Error: {e}")
        except requests.exceptions.Timeout as e:
            logging.error(f"超时: {e}")
            self.send_error(504, f"Timeout: {e}")
        except Exception as e:
            logging.error(f"代理错误: {e}")
            self.send_error(502, f"Proxy Error: {e}")

    def do_POST(self):
        # 有些订阅链接会用 POST
        self.do_GET()

    def log_message(self, format, *args):
        logging.info(f"{self.client_address[0]} - {format % args}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="订阅链接 UA 转发代理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                          # 测试模式 (httpbin)
  %(prog)s --port 8080                              # 指定端口
  %(prog)s --upstream "https://..." --ua "clash-verge/v2.5.3"  # 真实订阅
        """,
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.environ.get("PROXY_PORT", DEFAULT_PORT)),
        help=f"监听端口 (默认: {DEFAULT_PORT}, 环境变量: PROXY_PORT)",
    )
    parser.add_argument(
        "--upstream", "-u",
        default=os.environ.get("UPSTREAM_URL", ""),
        help="默认上游订阅链接。请求路径包含 http(s):// 时自动路由到路径中的链接",
    )
    parser.add_argument(
        "--ua", "-a",
        default=os.environ.get("CUSTOM_UA", DEFAULT_UA),
        help=f"自定义 User-Agent (默认: {DEFAULT_UA}, 环境变量: CUSTOM_UA)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="不验证 SSL 证书 (自签名证书时使用)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 设置日志
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # 确定上游 URL
    upstream = args.upstream.strip()
    if not upstream:
        upstream = TEST_UPSTREAM
        logging.warning("未指定上游 URL，使用测试地址 httpbin.org/headers")
        logging.warning("请用 --upstream 或环境变量 UPSTREAM_URL 设置真实订阅链接")

    # 配置 handler
    ProxyHandler.upstream_url = upstream
    ProxyHandler.custom_ua = args.ua
    ProxyHandler.verify_ssl = not args.no_verify_ssl

    # 启动服务器
    server = HTTPServer(("0.0.0.0", args.port), ProxyHandler)

    logging.info("=" * 60)
    logging.info("  订阅链接 UA 转发代理已启动")
    logging.info(f"  监听地址: http://0.0.0.0:{args.port}")
    logging.info(f"  默认上游: {upstream}")
    logging.info(f"  自定义 UA: {args.ua}")
    logging.info(f"  SSL 验证: {'关闭' if args.no_verify_ssl else '开启'}")
    logging.info("=" * 60)
    logging.info("任意上游用法 (直接将链接拼在路径中):")
    logging.info(f"  http://127.0.0.1:{args.port}/<https://your-upstream-url>")
    logging.info("")
    logging.info("按 Ctrl+C 停止服务器")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        logging.info("正在停止服务器...")
        server.shutdown()
        logging.info("服务器已停止")


if __name__ == "__main__":
    main()
