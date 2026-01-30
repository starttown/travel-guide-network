"""
MIT License

Copyright (c) 2026 starttown

Permission is hereby granted, free of charge, to any person obtaining a copy
"""

import sys
import psutil
import os
import subprocess
import signal
import json
import shutil
import time
import platform
from pathlib import Path
from datetime import datetime

# ================= UTF-8 强制设置 =================
# 设置环境变量以确保子进程输出中文不乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"


# ================= LLM 配置加载逻辑 =================
def load_llm_config_and_set_env():
    """
    读取 llm_config.json 并设置环境变量。
    如果文件不存在或读取失败，使用内置默认值。
    注意：此函数会修改全局 ENV 变量，确保子进程能获取到最新配置。
    """
    global ENV  # 关键：修改全局 ENV 字典，以便子进程继承

    config_file = NETWORK_DIR / "llm_config.json"

    # 1. 定义默认值（当配置文件不存在或缺少某项时使用）
    defaults = {
        "DEFAULT_LLM_PROVIDER": "custom",
        "DEFAULT_LLM_MODEL_NAME": "gpt-oss:20b",
        "DEFAULT_LLM_API_KEY": "not-required",
        "DEFAULT_LLM_BASE_URL": "http://localhost:11434/v1"
    }

    print("\n" + "=" * 60)
    print("🔧 [Config] 正在初始化 LLM 配置...")
    print(f"🔧 [Config] 配置文件路径: {config_file}")

    final_config = defaults.copy()

    # 2. 尝试读取并合并 JSON 配置
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            
            # 将用户配置覆盖到默认配置上
            final_config.update(user_config)
            print(f"🔧 [Config] ✅ 成功读取配置文件并覆盖默认值。")
            
        except json.JSONDecodeError as e:
            print(f"⚠️  [Config] ⚠️ JSON 格式错误 ({e})，将忽略配置文件使用默认值。")
        except Exception as e:
            print(f"⚠️  [Config] ⚠️ 读取文件失败 ({e})，将使用默认值。")
    else:
        print(f"⚠️  [Config] ⚠️ 配置文件不存在，将使用硬编码默认值。")

    # 3. 应用环境变量并打印详情
    print("🔧 [Config] ----------------------------------------")
    print("🔧 [Config] 最终生效的环境变量配置:")
    
    for key, value in final_config.items():
        str_val = str(value)

        # 写入全局 ENV 副本（子进程会读取这个）
        ENV[key] = str_val
        
        # 打印时隐藏 API Key，避免泄露
        display_val = str_val
        if "API_KEY" in key or "api_key" in key:
            display_val = "***HIDDEN***"
            
        print(f"   - {key} = {display_val}")
    
    print("🔧 [Config] ----------------------------------------")
    print("🔧 [Config] 配置加载完成，已写入环境变量。")
    print("=" * 60 + "\n")



# ================= 平台检测 =================
IS_WINDOWS = platform.system() == "Windows"

# ================= 路径解析核心逻辑 =================
def resolve_openagents_path():
    """
    查找 openagents 可执行文件路径
    优先使用环境变量 PATH，失败则报错
    """
    openagents_exe = shutil.which("openagents")
    if openagents_exe:
        return openagents_exe

    raise FileNotFoundError(
        "找不到 openagents 可执行文件。\n"
        "请确认 openagents 是否已通过 pip 安装并添加到环境变量中。"
    )

# ================= 全局路径设置 =================
try:
    OPENAGENTS_EXE = resolve_openagents_path()
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

NETWORK_DIR = Path(__file__).parent.resolve()
SCRIPT_DIR = NETWORK_DIR / "agents"
LOG_DIR = NETWORK_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ================= 进程管理类 =================
class ProcessManager:
    """子进程管理类：负责启动、停止及日志重定向"""

    def __init__(self):
        self.processes: dict[str, subprocess.Popen] = {}
        self.info: list[dict] = []

    def _get_log_path(self, name: str) -> Path:
        """生成带时间戳的日志文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return LOG_DIR / f"{name}_{timestamp}.log"

    def _popen_to_log(self, cmd: list[str], cwd: str, log_path: Path) -> subprocess.Popen:
        """启动子进程并重定向输出到日志文件"""
        log_file = open(log_path, "w", encoding="utf-8")
        
        # === 核心逻辑：创建进程组，确保父进程被杀时，子进程也能被系统清理 ===
        kwargs = {
            "cwd": cwd,
            "stdout": log_file,
            "stderr": subprocess.STDOUT,
            "env": ENV,
        }

        if IS_WINDOWS:
            # Windows: 创建新的进程组，使当前进程成为组长
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            # Linux/Mac: 使用 os.setsid 创建新会话
            kwargs["preexec_fn"] = os.setsid

        return subprocess.Popen(cmd, **kwargs)

    def start_network(self):
        """启动网络节点"""
        if not NETWORK_DIR.exists():
            raise ValueError(f"网络目录不存在: {NETWORK_DIR}")

        cmd = [OPENAGENTS_EXE, "network", "start", str(NETWORK_DIR)]
        log_file = self._get_log_path("network")
        proc = self._popen_to_log(cmd, cwd=str(NETWORK_DIR), log_path=log_file)

        self.processes["network"] = proc
        self.info.append({
            "type": "network", "pid": proc.pid, "log": str(log_file),
            "cwd": str(NETWORK_DIR), "status": "running"
        })

    def start_agent(self, yaml_name: str):
        """启动单个 Agent"""
        # === 修复点：先构造 Path 对象 ===
        yaml_file = SCRIPT_DIR / yaml_name
        
        if not yaml_file.exists():
            raise ValueError(f"Agent 配置不存在: {yaml_file}")

        cmd = [OPENAGENTS_EXE, "agent", "start", str(yaml_file)]
        
        # === 修复点：使用 yaml_file.stem 而不是 yaml_name.stem ===
        log_file = self._get_log_path(f"agent_{yaml_file.stem}")
        
        proc = self._popen_to_log(cmd, cwd=str(SCRIPT_DIR), log_path=log_file)

        self.processes[f"agent_{yaml_file.stem}"] = proc
        self.info.append({
            "type": "agent", "pid": proc.pid, "log": str(log_file),
            "cwd": str(SCRIPT_DIR), "status": "running"
        })

    def start_script(self, script_name: str):
        """运行本地 Python 脚本"""
        target_script = SCRIPT_DIR / script_name
        if not target_script.exists():
            raise ValueError(f"脚本不存在: {target_script}")

        cmd = [sys.executable, str(target_script)]
        log_file = self._get_log_path(f"script_{target_script.stem}")
        proc = self._popen_to_log(cmd, cwd=str(SCRIPT_DIR), log_path=log_file)

        self.processes[f"script_{target_script.stem}"] = proc
        self.info.append({
            "type": "script", "pid": proc.pid, "log": str(log_file),
            "cwd": str(SCRIPT_DIR), "status": "running"
        })

    def stop_all(self):
        """停止所有子进程并清理残留"""
        print("[ProcessManager] 正在停止所有服务...")

        # 1. 优先级最高：Windows 下向进程组发送 CTRL_BREAK_EVENT
        # 这会杀死整个进程树，非常高效
        if IS_WINDOWS:
            try:
                os.kill(os.getpid(), signal.CTRL_BREAK_EVENT)
                time.sleep(0.5) # 给系统一点时间处理信号
            except Exception:
                pass

        # 2. 正常停止记录在案的进程
        for name, proc in self.processes.items():
            try:
                if proc.poll() is None: # 如果进程还在运行
                    proc.terminate()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception:
                pass

        # 3. 防御性清理：遍历所有进程杀死特定的孤儿进程
        targets = ['weather_connector.py', 'travel_coordinator.py']
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                for target in targets:
                    if target in cmdline:
                        print(f"[ProcessManager] 清理残留进程 {proc.info['pid']} ({target})")
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.processes.clear()
        self.info.clear()

    def get_status_json(self) -> str:
        """获取进程状态 JSON"""
        return json.dumps(self.info, ensure_ascii=False, indent=2)


manager = ProcessManager()


# ================= 退出信号处理 =================
def cleanup(signum=None, frame=None):
    print("\n[Manager] 收到退出信号，正在清理...")
    manager.stop_all()
    print("[Manager] 已停止。")
    sys.exit(0)


if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, cleanup)
if hasattr(signal, "SIGINT"):
    signal.signal(signal.SIGINT, cleanup)


# ================= 主入口 =================
def _print_banner():
    print(f"[Info] OpenAgents: {OPENAGENTS_EXE}")
    print(f"[Info] Network Dir: {NETWORK_DIR}")
    print(f"[Info] Log Dir: {LOG_DIR}")


def _print_usage_example():
    print("\n" + "=" * 60)
    print("🎉 所有 Agents 已启动！系统正在守护中...")
    print("=" * 60)
    print("\n📝 使用方式:")
    print("  • 使用 travel_sender.py 发送旅游指南请求")
    print("  • 四个学院学生将根据各自的特质提供旅行建议")
    print("\n🏰 学院特质:")
    print("  🦁 格兰芬多: 勇敢冒险")
    print("  🐍 斯莱特林: 战略规划")
    print("  🦅 拉文克劳: 学习成长")
    print("  🦡 赫奇帕奇: 温馨包容")
    print("\n按 Ctrl+C 停止所有服务")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <all>")
        sys.exit(1)

    cmd_type = sys.argv[1]

    load_llm_config_and_set_env()
    
    _print_banner()

    if cmd_type == "all":
        print("=" * 60)
        print("🚀 启动完整系统")
        print("=" * 60)

        # 1. 启动网络
        print("\n📡 [1/3] 启动网络...")
        manager.start_network()
        time.sleep(1)  # 间隔1秒

        # 2. 启动四个学院学生
        print("\n🏰 [2/3] 启动学院 Agents...")
        
        print("  🦁 启动 Gryffindor...")
        manager.start_agent("gryffindor-student.yaml")
        time.sleep(1)

        print("  🐍 启动 Slytherin...")
        manager.start_agent("slytherin-student.yaml")
        time.sleep(1)

        print("  🦅 启动 Ravenclaw...")
        manager.start_agent("ravenclaw-student.yaml")
        time.sleep(1)

        print("  🦡 启动 Hufflepuff...")
        manager.start_agent("hufflepuff-student.yaml")
        time.sleep(1)

        # 3. 启动天气连接器
        print("\n🌤️  [3/3] 启动天气连接器...")
        manager.start_script("weather_connector.py")
        time.sleep(1)

        # Studio 启动选项（根据需求决定是否取消注释）
        # print("\n🖥️  [4/6] 启动 Studio...")
        # manager.start_studio()
        # time.sleep(1)

        _print_usage_example()

    else:
        print(f"未知命令: {cmd_type}，目前支持 'all'")
        sys.exit(1)

    print("<<<START_INFO>>>")
    print(manager.get_status_json())
    print("<<<END_INFO>>>")

    try:
        while True:
            pass
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("<<<START_INFO>>>")
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        print("<<<END_INFO>>>")
        manager.stop_all()
        sys.exit(1)
