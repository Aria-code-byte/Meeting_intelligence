#!/usr/bin/env python3
"""
快速导出工具 - 从浏览器 localStorage 导出会议数据
"""
import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webbrowser
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_export_server():
    """启动导出服务器"""
    # 切换到 exports 目录
    exports_dir = Path("/mnt/d/projects/Meeting_intelligence/exports")
    os.chdir(exports_dir)

    port = 8899
    server = HTTPServer(('localhost', port), CORSRequestHandler)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║           📤 会议数据导出工具                              ║
╠════════════════════════════════════════════════════════════╣
║  在浏览器中打开以下链接：                                  ║
║                                                          ║
║  http://localhost:8899/export_from_browser.html            ║
║                                                          ║
║  然后点击导出按钮即可下载会议数据                           ║
╚════════════════════════════════════════════════════════════╝

按 Ctrl+C 停止服务器
""")

    # 自动打开浏览器
    try:
        webbrowser.open(f'http://localhost:8899/export_from_browser.html')
    except:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        sys.exit(0)

if __name__ == "__main__":
    start_export_server()
