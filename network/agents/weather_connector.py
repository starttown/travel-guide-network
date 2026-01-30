#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from aiohttp import web

# OpenAgents 核心组件
from openagents.agents.worker_agent import WorkerAgent
from openagents.mods.coordination.task_delegation import TaskDelegationAdapter

# --- 配置与路径处理 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# --- 外部工具导入 ---
from tools.send_result import send_result_to_server
from tools.weather import get_weather_report

# --- 全局配置 ---
# 定义固定顺序：Gryffindor -> Slytherin -> Ravenclaw -> Hufflepuff
STUDENT_AGENTS = [
    "gryffindor-student",
    "slytherin-student",
    "ravenclaw-student",
    "hufflepuff-student"
]
TASK_TIMEOUT_SECONDS = 120


# --- 主服务类 (继承 WorkerAgent) ---
class WeatherCoordinatorAgent(WorkerAgent):
    """
    基于官方 Demo 架构的天气协调 Agent。
    """
    default_agent_id = "weather-connector"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.delegation_adapter = TaskDelegationAdapter()
        self.runner = None

    async def on_startup(self):
        self.delegation_adapter.bind_client(self.client)
        self.delegation_adapter.bind_connector(self.client.connector)
        self.delegation_adapter.bind_agent(self.agent_id)

        logging.info(f"✅ Agent '{self.agent_id}' started and adapters bound.")
        logging.info("🌐 Workflow: Receive HTTP Request -> Delegate to Students -> Send Results")

        app = web.Application()
        app.router.add_post("/generate", self.handle_http_request)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', 8888)
        await site.start()

        logging.info("🚀 HTTP Server started on http://0.0.0.0:8888")

    async def _delegate_task(self, assignee_id: str, description: str, project_id: str):
        """委派任务并返回 task_id"""
        result = await self.delegation_adapter.delegate_task(
            assignee_id=assignee_id,
            description=description,
            payload={"project_id": project_id}
        )

        if result and result.get("success") and "task_id" in result.get("data", {}):
            task_id = result["data"]["task_id"]
            logging.info(f"📤 Task {task_id} delegated to {assignee_id}")
            return task_id

        logging.error(f"❌ Failed to delegate to {assignee_id}: {result}")
        return None

    async def _wait_and_send_result(self, task_id: str, student_id: str):
        """
        等待任务完成并发送结果
        兼容两种事件名以防止误判
        """
        logging.info(f"⏳ [{student_id}] Watching task {task_id}...")

        try:
            event = await asyncio.wait_for(
                self.client.wait_event(
                    condition=lambda e: (
                        e.payload and
                        e.payload.get("task_id") == task_id and
                        e.event_name in ("task.notification.completed", "task.complete")
                    )
                ),
                timeout=TASK_TIMEOUT_SECONDS
            )

            if event:
                logging.info(f"✅ [{student_id}] Task {task_id} completed (Event: {event.event_name}).")
                result = event.payload.get("result")

                if isinstance(result, dict):
                    res_text = result.get("value", str(result))
                else:
                    res_text = str(result)

                # --- 修改点：上传任务完成情况 ---
                report = f"Agent: {student_id}\n{res_text}"
                send_result_to_server("weather-connector", report)
                # ------------------------------
                logging.info(f"📤 [{student_id}] Result sent.")
            else:
                # --- 修改点：上传无事件情况 ---
                err_msg = f"Task Status: Failed (No Event)\nAgent: {student_id}"
                logging.warning(err_msg)
                send_result_to_server("weather-connector", err_msg)

        except asyncio.TimeoutError:
            # --- 修改点：上传超时情况 ---
            err_msg = f"Task Status: Failed (Timeout)\nAgent: {student_id}\nTimeout: >{int(TASK_TIMEOUT_SECONDS)}s"
            logging.warning(f"⏰ {err_msg}")
            send_result_to_server("weather-connector", err_msg)
        except Exception as e:
            # --- 修改点：上传异常情况 ---
            err_msg = f"Task Status: Failed (Error)\nAgent: {student_id}\nException: {e}"
            logging.error(f"❌ {err_msg}", exc_info=True)
            send_result_to_server("weather-connector", err_msg)

    async def handle_http_request(self, request):
        """处理 HTTP POST /generate 请求"""
        try:
            data = await request.json()
            city = data.get("city")
            date_val = data.get("date")
        except Exception:
            return web.json_response({"status": "error", "message": "Invalid JSON"}, status=400)

        if not city:
            return web.json_response({"status": "error", "message": "Missing 'city'"}, status=400)

        logging.info(f"🚀 Received HTTP request: {city}, date: {date_val}")

        # 启动后台工作流 (不阻塞 HTTP 响应)
        asyncio.create_task(self.run_workflow(city, date_val))

        return web.json_response({"status": "ok", "message": "Request accepted, processing..."})

    async def run_workflow(self, city: str, date_val: str):
        """核心业务工作流 - 顺序执行版本"""
        project_id = f"manual-{city}-{int(asyncio.get_event_loop().time())}"

        try:
            # === Step 1: 获取天气 ===
            logging.info("=== WORKFLOW STARTED ===")
            logging.info(f"🌤️ Fetching weather for {city}...")

            weather_text = get_weather_report(city, date_val)

            # 立即发送天气报告
            send_result_to_server("weather-connector", f"{weather_text}")
            logging.info("📤 Weather report sent.")

            # === Step 2: 顺序委派任务 ===
            logging.info("🚀 Delegating tasks to students sequentially (One by One)...")

            for student_id in STUDENT_AGENTS:
                logging.info(f"🔄 Current turn: {student_id}")

                # --- 修改点：在每一个任务下发之前加1秒延时 ---
                await asyncio.sleep(1)
                logging.info(f"⏱️  Waited 1s before delegating to {student_id}...")
                # --------------------------------------------

                task_id = await self._delegate_task(
                    student_id,
                    f"Generate travel advice based on this weather:\n{weather_text}",
                    project_id
                )

                if task_id:
                    # 这里使用 await，会一直卡在这里，直到 _wait_and_send_result 返回
                    # 也就是必须等这个学生处理完，才会去循环下一个
                    await self._wait_and_send_result(task_id, student_id)
                else:
                    # 委派失败，上传任务失败情况
                    err_msg = f"Task Status: Failed (Delegation)\nAgent: {student_id}"
                    logging.error(err_msg)
                    send_result_to_server("weather-connector", err_msg)

            logging.info("🏁 Workflow finished (All students processed in order).")

        except Exception as e:
            logging.error(f"💥 Workflow crashed: {e}", exc_info=True)
            send_result_to_server("weather-connector", f"System Error: {e}")


async def main():
    """启动 Agent"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 实例化 Agent
    agent = WeatherCoordinatorAgent()

    try:
        # 启动 Agent
        await agent.async_start(
            network_host="localhost",
            network_port=8700,
            password_hash="bf24385098410391a81d92b2de72d3a2946d24f42ee387e51004a868281a2408"
        )

        print("Weather Coordinator Agent (WorkerAgent) running...")
        print("Mode: Sequential (One by One)")
        print("HTTP Interface: http://0.0.0.0:8888/generate")
        print("Press Ctrl+C to stop.")

        # 保持 Agent 运行
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await agent.async_stop()


if __name__ == "__main__":
    asyncio.run(main())
