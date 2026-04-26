# qwen-proxy

纯 Python 实现的 OpenAI 兼容 API 代理，零依赖（仅用标准库）。

```
客户端 → proxy.py:8765 → Qwen3.6-35B (58.23.129.98:8001)
```

## 亮点

- **零依赖** — 只有 Python 3 标准库，`http.server` + `http.client`
- **流式 SSE** — 完整转发 `stream=true` 的 chunked 响应
- **抓包级日志** — 每个请求/响应打印原始字节、Hex 转储、文本内容（像 Wireshark）
- **GET 转发** — `/v1/models` 等端点到上游

## 快速开始

```bash
# 直接运行
python3 proxy.py

# 后台运行
nohup python3 proxy.py > /tmp/proxy.log 2>&1 &
```

默认监听 `0.0.0.0:8765`，转发到 `58.23.129.98:8001`。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/chat/completions` | POST | 聊天补全（支持 `stream: true`） |
| `/v1/models` | GET | 列出可用模型 |
| `/health` | GET | 健康检查 |

### 使用示例

```bash
# 非流式
curl -X POST http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b","messages":[{"role":"user","content":"你好"}],"max_tokens":100}'

# 流式
curl -N -X POST http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b","messages":[{"role":"user","content":"你好"}],"max_tokens":100,"stream":true}'

# 模型列表
curl http://localhost:8765/v1/models

# 健康检查
curl http://localhost:8765/health
```

## 日志格式

每条请求/响应打印三部分：

```
📥 INCOMING (291 bytes)
  RAW BYTES:  POST /v1/chat/completions HTTP/1.1...
  HEX DUMP:   0000: 50 4f 53 54 20 2f...POST /v1/chat/co
  TEXT:       0: POST /v1/chat/completions HTTP/1.1
              1: Host: localhost:8765
              ...

📤 OUTGOING (148 bytes)
  RAW BYTES:  HTTP/1.1 200 OK...
  HEX DUMP:   0000: 48 54 54 50 2f...HTTP/1.1 200 OK.
  TEXT:       0: HTTP/1.1 200 OK
              ...
```

## 配置

编辑 `proxy.py` 顶部常量：

```python
TARGET_HOST = "58.23.129.98"   # 上游 API 地址
TARGET_PORT = 8001              # 上游 API 端口
API_KEY     = "sk-78sadn09bjawde123e"  # 上游 API Key
LISTEN_PORT = 8765              # 本地监听端口
```

## 文件结构

```
proxy-config/
├── proxy.py                  # 核心代理（唯一运行的文件）
├── docker-compose.yml        # 旧版 Nginx Docker 部署（已弃用）
├── docker-compose-logging.yml
├── nginx.conf                # 旧版 Nginx 配置（已弃用）
├── nginx-logging.conf
├── start.sh                  # 旧版启动脚本（已弃用）
├── monitor.py                # 旧版监控（已弃用）
├── log-analyzer.py           # 旧版日志分析（已弃用）
├── log-viewer.sh             # 旧版日志查看（已弃用）
├── logs/                     # 旧版日志目录
└── README.md
```

> **注**: `proxy.py` 是唯一实际使用的文件。其余为早期 Nginx/Docker 方案的遗留文件，计划清理。

## 上游 API 信息

- 模型: `qwen3.6-35b`
- 引擎: vLLM
- 上下文长度: 262144 (256K)
- 运行位置: `58.23.129.98:8001`
