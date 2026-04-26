#!/usr/bin/env python3
"""Nginx日志分析工具"""

import re
from collections import Counter
import argparse
import sys

class NginxLogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        
    def parse_log_line(self, line):
        """解析Nginx日志行"""
        # 匹配详细日志格式
        pattern = r'(?P<ip>\S+) - (?P<user>\S+) \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" ' \
                 r'(?P<status>\d+) (?P<size>\d+) "(?P<referer>[^"]*)" "(?P<agent>[^"]*)" ' \
                 r'rt=(?P<request_time>[^ ]+) uct="(?P<upstream_connect_time>[^"]*)" ' \
                 r'urt="(?P<upstream_response_time>[^"]*)"'
        
        match = re.match(pattern, line)
        if match:
            return match.groupdict()
        return None
    
    def analyze_logs(self):
        """分析日志文件"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"❌ 日志文件不存在: {self.log_file}")
            return
        
        print(f"📊 分析日志: {self.log_file}")
        print(f"📈 总行数: {len(lines)}")
        print("="*60)
        
        # 统计信息
        status_codes = Counter()
        request_times = []
        clients = Counter()
        endpoints = Counter()
        
        valid_lines = 0
        
        for line in lines[-1000:]:  # 分析最近1000行
            data = self.parse_log_line(line)
            if data:
                valid_lines += 1
                
                # 统计状态码
                status_codes[data['status']] += 1
                
                # 统计客户端IP
                clients[data['ip']] += 1
                
                # 统计请求时间
                try:
                    rt = float(data['request_time'])
                    request_times.append(rt)
                except:
                    pass
                
                # 统计端点
                request = data['request']
                if ' ' in request:
                    method, endpoint, _ = request.split(' ', 2)
                    endpoints[f"{method} {endpoint}"] += 1
        
        # 输出统计结果
        print("🔄 状态码分布:")
        for code, count in status_codes.most_common():
            print(f"   {code}: {count} 次")
        
        print(f"\n👥 客户端TOP 10:")
        for ip, count in clients.most_common(10):
            print(f"   {ip}: {count} 次")
        
        print(f"\n🎯 接口调用TOP 10:")
        for endpoint, count in endpoints.most_common(10):
            print(f"   {endpoint}: {count} 次")
        
        if request_times:
            avg_time = sum(request_times) / len(request_times)
            max_time = max(request_times)
            print(f"\n⏱️  请求时间统计:")
            print(f"   平均: {avg_time:.3f}s")
            print(f"   最大: {max_time:.3f}s")
            print(f"   慢请求(>1s): {sum(1 for rt in request_times if rt > 1)} 次")
        
        print(f"\n✅ 有效日志行: {valid_lines}")

def main():
    parser = argparse.ArgumentParser(description='Nginx日志分析工具')
    parser.add_argument('log_file', help='日志文件路径')
    parser.add_argument('--tail', type=int, default=1000, help='分析最近N行')
    
    args = parser.parse_args()
    
    analyzer = NginxLogAnalyzer(args.log_file)
    analyzer.analyze_logs()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 默认分析access.log
        analyzer = NginxLogAnalyzer("/var/log/nginx/access.log")
        analyzer.analyze_logs()
    else:
        main()