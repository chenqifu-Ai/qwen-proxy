#!/bin/bash

# 🔍 Nginx日志查看工具

echo "📊 Qwen代理日志查看器"
echo "======================"

LOG_DIR="/var/log/nginx"
CONTAINER_LOG_DIR="./logs"

# 检查日志目录
if [ -d "$LOG_DIR" ]; then
    echo "📁 系统日志目录: $LOG_DIR"
    CURRENT_LOG_DIR="$LOG_DIR"
elif [ -d "$CONTAINER_LOG_DIR" ]; then
    echo "🐳 容器日志目录: $CONTAINER_LOG_DIR"
    CURRENT_LOG_DIR="$CONTAINER_LOG_DIR"
else
    echo "❌ 未找到日志目录"
    exit 1
fi

echo ""
echo "🎯 可用日志文件:"
echo "================"
ls -la "$CURRENT_LOG_DIR"/*.log 2>/dev/null | awk '{print "   " $9}'

echo ""
echo "🚀 快速查看命令:"
echo "================"
echo "1. 实时访问日志:    tail -f $CURRENT_LOG_DIR/access.log"
echo "2. 流式请求日志:    tail -f $CURRENT_LOG_DIR/streaming.log"  
echo "3. 错误日志:        tail -f $CURRENT_LOG_DIR/error.log"
echo "4. API访问日志:     tail -f $CURRENT_LOG_DIR/api-access.log"
echo "5. JSON格式日志:    tail -f $CURRENT_LOG_DIR/access.json"
echo "6. 健康检查日志:    tail -f $CURRENT_LOG_DIR/health.log"
echo ""

echo "🔍 高级日志分析:"
echo "================"
echo "7. 查看最近错误:    grep -i error $CURRENT_LOG_DIR/error.log | tail -20"
echo "8. 查看慢请求:      awk '\$NF > 1 {print \$0}' $CURRENT_LOG_DIR/access.log | tail -10"
echo "9. 统计状态码:      awk '{print \$9}' $CURRENT_LOG_DIR/access.log | sort | uniq -c"
echo "10. 查看客户端IP:   awk '{print \$1}' $CURRENT_LOG_DIR/access.log | sort | uniq -c | sort -nr | head -10"
echo ""

echo "📈 实时监控命令:"
echo "================"
echo "R. 实时监控所有日志:  multitail $CURRENT_LOG_DIR/*.log"
echo "L. 监听流式请求:      tail -f $CURRENT_LOG_DIR/streaming.log | grep -E \"(POST|stream)\""
echo "T. 跟踪请求时间:      tail -f $CURRENT_LOG_DIR/access.log | awk '{printf \"时间: %s s | 状态: %s | 大小: %s bytes\\n\", \$(NF-2), \$9, \$10}'"