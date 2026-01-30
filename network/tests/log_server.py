#!/usr/bin/env python3
"""
Robust Log Server - Receives results via HTTP and prints them.
Guaranteed not to crash.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
import datetime

class LogHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # 禁用默认日志

    def do_POST(self):
        if self.path == '/log':
            try:
                # 1. 读取数据
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                
                # 2. 解析 JSON (带容错)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError:
                    print("❌ [Server] 收到非法 JSON，忽略。")
                    self._respond(400, {"error": "Invalid JSON"})
                    return

                # 3. 美化打印
                agent_name = data.get('agent', 'Unknown')
                content = data.get('content', '')
                
                print("\n" + "="*70)
                print(f"📩 [{datetime.datetime.now().strftime('%H:%M:%S')}] 收到来自 '{agent_name}' 的建议:")
                print("="*70)
                print(content)
                print("="*70 + "\n")

                # 4. 响应成功
                self._respond(200, {"status": "received"})

            except Exception as e:
                # 捕获所有异常，防止服务器崩溃
                print(f"⚠️ [Server] 内部错误 (但服务未中断): {e}")
                self._respond(500, {"error": "Internal Server Error"})
        else:
            self._respond(404, {"error": "Not Found"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server(port=9999):
    server_address = ('', port)
    httpd = HTTPServer(server_address, LogHandler)
    print(f"🚀 日志服务器运行在 http://localhost:{port}/log")
    print("💡 等待学生 Agent 发送建议...\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已关闭")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
