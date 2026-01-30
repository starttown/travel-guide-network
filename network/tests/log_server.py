#!/usr/bin/env python3
import asyncio
from aiohttp import web
from datetime import datetime

async def handle_log(request):
    """处理 /log 路径的 POST 请求"""
    try:
        # 1. 解析 JSON 数据
        data = await request.json()
        
        agent_id = data.get('agent', 'Unknown')
        content = data.get('content', '')
        timestamp = datetime.now().strftime('%H:%M:%S')

        # 2. 格式化打印接收到的消息
        print("\n" + "=" * 60)
        print(f"📩 [{timestamp}] 收到来自 Agent: {agent_id} 的消息")
        print("-" * 60)
        print(content)
        print("=" * 60 + "\n")

        # 3. 返回成功响应给发送方
        return web.json_response({"status": "success", "message": "Logged"})

    except Exception as e:
        print(f"❌ 处理请求时出错: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=400)

async def start_server():
    """启动日志服务器"""
    app = web.Application()
    # 注册路由
    app.router.add_post('/log', handle_log)

    runner = web.AppRunner(app)
    await runner.setup()
    
    # 绑定到 0.0.0.0:9999
    # 注意：如果你的 weather_connector 和此服务端在同一台机器，可以使用 localhost
    site = web.TCPSite(runner, '0.0.0.0', 9999)
    await site.start()

    print("🚀 日志服务器已启动")
    print("📍 监听地址: http://0.0.0.0:9999/log")
    print("📝 等待接收消息...")
    print("   (按 Ctrl+C 停止服务器)")
    
    try:
        # 保持服务器运行
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n⏹️  服务器正在关闭...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(start_server())
