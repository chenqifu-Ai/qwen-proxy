#!/usr/bin/env python3
"""代理监控脚本"""

import requests
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    filename='logs/monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_health():
    """检查代理健康状态"""
    try:
        response = requests.get('http://localhost:8765/health', timeout=5)
        if response.status_code == 200:
            return True, "健康"
        else:
            return False, f"状态码: {response.status_code}"
    except Exception as e:
        return False, f"连接错误: {e}"

def check_api():
    """检查API连接"""
    try:
        response = requests.post(
            'http://localhost:8765/v1/chat/completions',
            json={
                "model": "qwen3.6-35b",
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, "API正常"
        else:
            return False, f"API状态码: {response.status_code}"
    except Exception as e:
        return False, f"API错误: {e}"

def main():
    """主监控循环"""
    print("🔍 启动代理监控服务")
    logging.info("监控服务启动")
    
    while True:
        # 健康检查
        health_ok, health_msg = check_health()
        
        # API检查
        api_ok, api_msg = check_api()
        
        # 记录状态
        status = "✅" if health_ok and api_ok else "❌"
        log_msg = f"{status} 健康: {health_msg} | API: {api_msg}"
        
        if health_ok and api_ok:
            logging.info(log_msg)
        else:
            logging.error(log_msg)
            print(f"{datetime.now()} - {log_msg}")
        
        # 每分钟检查一次
        time.sleep(60)

if __name__ == "__main__":
    main()