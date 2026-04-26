#!/bin/bash

# 🎯 启动带详细日志的Qwen代理

echo "📊 启动详细日志代理"
echo "📡 端口: 8765"
echo "🎯 目标: 58.23.129.98:8000"
echo "📝 日志级别: DEBUG"

# 创建详细的日志目录结构
mkdir -p logs/
mkdir -p logs/archive/

# 检查Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker未安装，使用系统Nginx"
    
    if command -v nginx >/dev/null 2>&1; then
        # 备份原配置
        if [ -f /etc/nginx/nginx.conf ]; then
            backup_file="/etc/nginx/nginx.conf.backup.$(date +%Y%m%d%H%M%S)"
            sudo cp /etc/nginx/nginx.conf "$backup_file"
            echo "✅ 原配置已备份: $backup_file"
        fi
        
        # 使用详细日志配置
        sudo cp nginx-logging.conf /etc/nginx/nginx.conf
        
        # 创建日志目录
        sudo mkdir -p /var/log/nginx/
        sudo chmod -R 755 /var/log/nginx/
        
        # 重启Nginx
        if sudo systemctl restart nginx 2>/dev/null || sudo service nginx restart 2>/dev/null; then
            echo "✅ Nginx已重启（详细日志模式）"
        else
            echo "❌ Nginx重启失败"
            exit 1
        fi
    else
        echo "❌ 系统未安装Nginx"
        exit 1
    fi
else
    echo "✅ Docker已安装，使用容器部署"
    
    # 停止现有容器
    if docker ps | grep -q "qwen-proxy"; then
        echo "🔄 停止现有容器"
        docker stop qwen-proxy-logs 2>/dev/null || true
        docker rm qwen-proxy-logs 2>/dev/null || true
    fi
    
    # 使用详细日志配置启动
    docker-compose -f docker-compose-logging.yml up -d
    echo "✅ Docker代理已启动（详细日志模式）"
fi

# 等待启动
sleep 3

echo ""
echo "🎉 详细日志代理部署完成"
echo ""
echo "📁 日志目录:"
if [ -d "/var/log/nginx" ]; then
    echo "   /var/log/nginx/"
    ls -la /var/log/nginx/*.log 2>/dev/null | awk '{print "   " $9}'
elif [ -d "./logs" ]; then
    echo "   ./logs/"
    ls -la ./logs/*.log 2>/dev/null | awk '{print "   " $9}'
fi

echo ""
echo "🔍 日志查看命令:"
echo "   tail -f /var/log/nginx/access.log"
echo "   tail -f /var/log/nginx/error.log"
echo "   tail -f /var/log/nginx/streaming.log"
echo ""
echo "📊 日志分析:"
echo "   ./log-viewer.sh"
echo "   python3 log-analyzer.py"

echo ""
echo "🌐 健康检查:"
echo "   curl http://localhost:8765/health"
echo "   curl http://localhost:8765/nginx_status"