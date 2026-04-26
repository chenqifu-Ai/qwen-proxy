# 🚀 Qwen3.6-35B 流式代理配置

## 📋 概述

专为 Qwen3.6-35B API 设计的**高性能流式代理**，支持：
- ✅ 流式传输 (SSE)
- ✅ 负载均衡
- ✅ 长连接保持
- ✅ 自动重连
- ✅ 健康监控

## 🎯 配置详情

### 网络架构
```
客户端 → Nginx (8765) → Qwen3.6-35B (58.23.129.98:8000)
```

### 核心特性
- **端口**: 8765
- **目标**: 58.23.129.98:8000  
- **API密钥**: sk-78sadn09bjawde123e
- **超时**: 300秒
- **流式**: 完全支持

## 🚀 快速开始

### 方法一：Docker部署（推荐）
```bash
cd /root/downloads/proxy-config

# 启动代理
chmod +x start.sh
./start.sh

# 或者直接使用 docker-compose
docker-compose up -d
```

### 方法二：系统Nginx部署
```bash
# 复制配置
sudo cp nginx.conf /etc/nginx/nginx.conf

# 重启Nginx
sudo systemctl restart nginx
```

## 📊 监控管理

### 健康检查
```bash
curl http://localhost:8765/health
```

### 状态监控
```bash
curl http://localhost:8765/nginx_status
```

### 日志查看
```bash
tail -f logs/access.log
tail -f logs/error.log
```

## 🎯 API使用示例

### 普通请求
```bash
curl -X POST http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

### 流式请求
```bash
curl -X POST http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "qwen3.6-35b", 
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100,
    "stream": true
  }'
```

## ⚙️ 配置优化

### 流式传输关键配置
```nginx
proxy_buffering off;      # 禁用缓冲
proxy_request_buffering off;
keepalive_timeout 300s;   # 长连接超时
proxy_read_timeout 300s;  # 代理读超时
```

### 性能优化
```nginx
worker_processes auto;     # 自动工作进程
worker_connections 1024;   # 每个进程连接数
use epoll;                # 高性能事件模型
multi_accept on;          # 多连接接受
```

## 🔧 故障排除

### 常见问题
1. **流式中断**: 检查 `proxy_buffering` 是否关闭
2. **连接超时**: 调整 `proxy_read_timeout`
3. **认证失败**: 确认API密钥正确

### 日志调试
```bash
# 查看错误日志
tail -f logs/error.log

# 查看访问日志  
tail -f logs/access.log
```

## 📁 文件结构
```
proxy-config/
├── nginx.conf          # Nginx主配置
├── docker-compose.yml   # Docker部署配置
├── start.sh            # 启动脚本
├── monitor.py          # 监控脚本
└── README.md           # 说明文档
```

## 🎯 性能指标
- ✅ 支持100+并发连接
- ✅ 300秒长连接保持  
- ✅ 实时流式传输
- ✅ 自动故障恢复

---
**最后更新**: 2026-04-26
**版本**: v1.0