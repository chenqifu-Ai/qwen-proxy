#!/bin/bash

# Qwen3.6-35B 代理启动脚本

echo "🚀 启动 Qwen3.6-35B 流式代理"
echo "📡 端口: 8765"
echo "🎯 目标: 58.23.129.98:8000"
echo "🔑 API密钥: sk-78sadn09bjawde123e"

# 创建日志目录
mkdir -p logs

# 检查 Docker 是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker 未安装，尝试使用系统 Nginx"
    
    # 检查 Nginx
    if command -v nginx >/dev/null 2>&1; then
        echo "✅ 发现系统 Nginx"
        # 备份原有配置
        if [ -f /etc/nginx/nginx.conf ]; then
            sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d%H%M%S)
        fi
        # 复制配置
        sudo cp nginx.conf /etc/nginx/nginx.conf
        # 重启 Nginx
        sudo systemctl restart nginx || sudo service nginx restart
        echo "✅ Nginx 代理已启动"
    else
        echo "❌ 系统未安装 Nginx"
        echo "📖 请安装 Nginx 或 Docker"
        exit 1
    fi
else
    echo "✅ Docker 已安装，使用容器部署"
    
    # 检查是否已运行
    if docker ps | grep -q "qwen-proxy"; then
        echo "🔄 停止现有容器"
        docker stop qwen-proxy
        docker rm qwen-proxy
    fi
    
    # 启动代理
    docker-compose up -d
    echo "✅ Docker 代理已启动"
fi

# 等待服务启动
sleep 2

# 测试连接
echo "🧪 测试代理连接..."
if curl -s http://localhost:8765/health >/dev/null 2>&1; then
    echo "✅ 代理健康检查通过"
else
    echo "❌ 代理健康检查失败"
fi

# 测试 API 连接
if curl -s -X POST http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b","messages":[{"role":"user","content":"test"}],"max_tokens":10}' \
  >/dev/null 2>&1; then
    echo "✅ API 连接测试通过"
else
    echo "⚠️  API 连接测试失败（可能是认证问题）"
fi

echo ""
echo "🎉 代理部署完成"
echo "📊 访问地址: http://localhost:8765/v1/"
echo "❤️  健康检查: http://localhost:8765/health"
echo "📈 状态监控: http://localhost:8765/nginx_status"
echo ""
echo "📝 日志目录: ./logs/"
echo "⚙️  配置文件: ./nginx.conf"