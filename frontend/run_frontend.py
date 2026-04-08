"""
多线程 HTTP 服务器，用于提供用户端页面
解决 file:// 协议的 CORS 和 API 调用问题
"""

import http.server
import socketserver
import webbrowser
import os

# 配置
PORT = 5175
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 添加 CORS 头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    os.chdir(DIRECTORY)

    with ThreadingHTTPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"[OK] 用户端服务器已启动!")
        print(f"[>] 访问地址: http://localhost:{PORT}")
        print(f"[*] 目录: {DIRECTORY}")
        print(f"[x] 按 Ctrl+C 停止服务器")
        print()

        # 自动打开浏览器
        url = f"http://localhost:{PORT}"
        webbrowser.open(url)
        print(f"[*] 已自动打开浏览器: {url}")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n[x] 服务器已停止")
