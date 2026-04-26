#!/usr/bin/env python3
"""
Qwen3.6-35B 流式代理 (端口 8765 → 58.23.129.98:8001)
纯标准库实现，无需第三方依赖
支持：流式SSE、输入/输出日志分离、时间戳
"""

import json
import sys
import signal
import http.server
import http.client
import urllib.parse
from datetime import datetime, timezone, timedelta

TARGET_HOST = "58.23.129.98"
TARGET_PORT = 8001
API_KEY = "sk-78sadn09bjawde123e"
LISTEN_PORT = 8765

tz_cn = timezone(timedelta(hours=8))

def ts():
    return datetime.now(tz_cn).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def log(tag, msg):
    print(f"[{ts()}] [{tag:>5}] {msg}", flush=True)

def trunc(s, n=200):
    s = str(s)
    return s[:n] + ("..." if len(s) > n else "")

def hexdump(data, offset=0):
    """生成漂亮的 hex dump，每行 16 字节"""
    lines = []
    ascii_buf = ""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        # 右对齐补空格
        hex_str = hex_str.ljust(47)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        addr = f"{offset + i:04x}"
        lines.append(f" {addr}: {hex_str} {ascii_str}")
    return "\n".join(lines)

def dump_incoming(method, path, headers, body):
    """记录完整的入站请求（包含原始字节/hex/文本）"""
    # 重建原始 HTTP 请求
    req_line = f"{method} {path} HTTP/1.1"
    header_lines = [f"{k}: {v}" for k, v in headers.items()]
    raw = (req_line + "\r\n" + "\r\n".join(header_lines) + "\r\n\r\n").encode() + body
    size = len(raw)
    print(f"\n{'='*80}", flush=True)
    print(f" [{ts()}] 📥 INCOMING ({size} bytes) {'='*60}", flush=True)
    print(f" RAW BYTES:\n {raw[:2000].decode('utf-8', 'replace')}", flush=True)
    print(f" HEX DUMP:")
    print(hexdump(raw), flush=True)
    print(f" TEXT CONTENT:")
    for i, line in enumerate(raw.decode("utf-8", "replace").split("\r\n")):
        print(f"  {i}: {line}", flush=True)
    print(f"{'='*80}", flush=True)

def dump_outgoing(status, reason, headers, body):
    """记录完整的出站响应（包含原始字节/hex/文本）"""
    status_line = f"HTTP/1.1 {status} {reason}"
    # headers 可能是 list of tuples 或 dict
    if isinstance(headers, dict):
        header_items = headers.items()
    else:
        header_items = headers
    header_lines = [f"{k}: {v}" for k, v in header_items]
    raw = (status_line + "\r\n" + "\r\n".join(header_lines) + "\r\n\r\n").encode() + (body or b"")
    size = len(raw)
    print(f"{'='*80}", flush=True)
    print(f" [{ts()}] 📤 OUTGOING ({size} bytes) {'='*60}", flush=True)
    print(f" RAW BYTES:\n {raw[:2000].decode('utf-8', 'replace')}", flush=True)
    print(f" HEX DUMP:")
    print(hexdump(raw), flush=True)
    print(f" TEXT CONTENT:")
    for i, line in enumerate(raw.decode("utf-8", "replace").split("\r\n")):
        print(f"  {i}: {line}", flush=True)
    print(f"{'='*80}", flush=True)

# ── 代理处理核心 ──

def proxy_normal(path, req_body, req_headers):
    """非流式转发"""
    conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=300)
    try:
        conn.request("POST", path, body=req_body, headers=req_headers)
        resp = conn.getresponse()
        resp_body = resp.read()
        status = resp.status
        reason = resp.reason
        headers = [(k, v) for k, v in resp.getheaders() if k.lower() not in ("transfer-encoding", "content-encoding")]
        dump_outgoing(status, reason, headers, resp_body)
        return status, headers, resp_body
    except Exception as e:
        err_body = json.dumps({"error": str(e)}).encode()
        dump_outgoing(502, "Bad Gateway", [("Content-Type", "application/json")], err_body)
        return 502, [("Content-Type", "application/json")], err_body
    finally:
        conn.close()

def proxy_stream(path, req_body, req_headers, wfile):
    """流式 SSE 转发"""
    conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=300)
    try:
        conn.request("POST", path, body=req_body, headers=req_headers)
        resp = conn.getresponse()

        log("STREAM", f"后端 HTTP {resp.status}")
        if resp.status != 200:
            err_body = resp.read().decode("utf-8", errors="replace")[:500]
            log("STREAM", f"后端错误: {err_body}")
            wfile.write(f"data: {json.dumps({'error': err_body})}\n\n".encode())
            wfile.write(b"data: [DONE]\n\n")
            wfile.flush()
            return

        # 构建响应头
        out_headers = [
            ("Content-Type", "text/event-stream; charset=utf-8"),
            ("Cache-Control", "no-cache"),
            ("Connection", "keep-alive"),
            ("Access-Control-Allow-Origin", "*"),
        ]
        # dump 出站响应头
        dump_outgoing(200, "OK", out_headers, None)

        # 发送响应头 (SSE)
        wfile.write(b"HTTP/1.1 200 OK\r\n")
        for k, v in out_headers:
            wfile.write(f"{k}: {v}\r\n".encode())
        wfile.write(b"\r\n")
        wfile.flush()

        chunk_count = 0
        while True:
            chunk = resp.read(4096)
            if not chunk:
                break
            try:
                wfile.write(chunk)
                wfile.flush()
                chunk_count += 1
                if chunk_count <= 3 or chunk_count % 30 == 0:
                    trimmed = chunk.decode("utf-8", "replace")[:120].replace("\n", "\\n")
                    log("STREAM", f"chunk #{chunk_count}: {trimmed}")
            except (BrokenPipeError, ConnectionResetError):
                log("STREAM", f"客户端断开 (chunk #{chunk_count})")
                break

        log("STREAM", f"流结束，共 {chunk_count} 个chunk")
    except Exception as e:
        log("STREAM", f"异常: {e}")
        try:
            wfile.write(f"data: {json.dumps({'error': str(e)})}\n\n".encode())
            wfile.write(b"data: [DONE]\n\n")
            wfile.flush()
        except:
            pass
    finally:
        conn.close()


# ── HTTP 服务器 ──

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._cors_headers()
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "ts": ts()}).encode())
            return
        # 代理 GET 请求到上游（/v1/models, /v1/models/xxx 等）
        self._proxy_get(self.path)

    def _proxy_get(self, path):
        """转发 GET 请求到上游"""
        conn = http.client.HTTPConnection(TARGET_HOST, TARGET_PORT, timeout=30)
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Host": f"{TARGET_HOST}:{TARGET_PORT}",
            }
            conn.request("GET", path, headers=headers)
            resp = conn.getresponse()
            resp_body = resp.read()
            headers_out = [(k, v) for k, v in resp.getheaders() if k.lower() not in ("transfer-encoding", "content-encoding")]
            dump_outgoing(resp.status, resp.reason, headers_out, resp_body)
            self.send_response(resp.status)
            for k, v in headers_out:
                self.send_header(k, v)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            err = json.dumps({"error": str(e)}).encode()
            dump_outgoing(502, "Bad Gateway", [("Content-Type", "application/json")], err)
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(err)
        finally:
            conn.close()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        req_body = self.rfile.read(content_len) if content_len > 0 else b""

        # 解析请求体，判断是否流式
        is_stream = False
        try:
            req_json = json.loads(req_body)
            is_stream = req_json.get("stream", False)
        except:
            pass

        # 完整 dump 入站请求（原始字节/hex/文本）
        headers_dict = {k: v for k, v in self.headers.items()}
        dump_incoming("POST", self.path, headers_dict, req_body)

        # 构建上游请求头 (去掉Host和Connection, 添加Authorization)
        req_headers = {}
        for k, v in self.headers.items():
            kl = k.lower()
            if kl not in ("host", "connection", "transfer-encoding", "content-length"):
                req_headers[k] = v
        req_headers["Authorization"] = f"Bearer {API_KEY}"
        req_headers["Host"] = f"{TARGET_HOST}:{TARGET_PORT}"

        if is_stream:
            proxy_stream(self.path, req_body, req_headers, self.wfile)
        else:
            status, headers, resp_body = proxy_normal(self.path, req_body, req_headers)
            self.send_response(status)
            for k, v in headers:
                if k.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                    self.send_header(k, v)
            self._cors_headers()
            self.end_headers()
            self.wfile.write(resp_body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def log_message(self, format, *args):
        pass  # 禁用默认日志，用我们的格式


def run():
    server = http.server.HTTPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler)
    log("INFO", f"🚀 代理启动: 0.0.0.0:{LISTEN_PORT} → {TARGET_HOST}:{TARGET_PORT}")
    log("INFO", f"🔑 API Key: {API_KEY[:8]}...")
    log("INFO", f"📋 日志格式: [时间] [REQ |RESP |STREAM|INFO] 内容")
    log("INFO", "")
    log("INFO", f"💡 流式: curl -N -X POST http://localhost:{LISTEN_PORT}/v1/chat/completions \\")
    log("INFO", f'   -H "Content-Type: application/json" \\')
    log("INFO", f'   -d \'{{"model":"qwen3.6-35b","messages":[{{"role":"user","content":"你好"}}],"stream":true}}\'')
    log("INFO", "")
    log("INFO", f"❤️  健康检查: curl http://localhost:{LISTEN_PORT}/health")
    print("-" * 60, flush=True)

    def shutdown(sig, frame):
        log("INFO", "收到退出信号，关闭服务器...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        log("INFO", "服务器已关闭")

if __name__ == "__main__":
    run()
