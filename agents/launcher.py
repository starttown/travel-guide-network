"""
MIT License

Copyright (c) 2026 starttown

Permission is hereby granted, free of charge, to any person obtaining a copy
"""

import sys
import os
import subprocess
import signal
import json
from pathlib import Path
from datetime import datetime

# ================= UTF-8 强制设置 =================
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"

# ================= 路径解析核心逻辑 =================
def resolve_openagents_path():
    """解析 openagents 的路径（Linux版本）。"""
    # 在Linux中，通常可执行文件在/usr/local/bin或~/.local/bin
    possible_paths = [
        "/usr/local/bin/openagents",
        os.path.expanduser("~/.local/bin/openagents"),
        "/usr/bin/openagents"
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path
    
    # 检查PATH环境变量
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(path, "openagents")
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return full_path
    
    raise FileNotFoundError(
        f"找不到 openagents 可执行文件。\n"
        f"已在以下位置搜索:\n"
        f"1. /usr/local/bin/openagents\n"
        f"2. ~/.local/bin/openagents\n"
        f"3. /usr/bin/openagents\n"
        f"4. PATH 环境变量中的路径\n"
        f"请确认 openagents 是否已安装。"
    )

# 全局路径变量
try:
    OPENAGENTS_EXE = resolve_openagents_path()
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent.resolve()
# 获取网络目录 (脚本目录的上一级)
NETWORK_DIR = SCRIPT_DIR.parent.resolve()
# 日志目录
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ================= 进程管理类 =================
class ProcessManager:
    def __init__(self):
        self.processes = {} 
        self.info = []      
    
    def _get_log_path(self, name):
        """生成带时间戳的日志文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return LOG_DIR / f"{name}_{timestamp}.log"
    
    def start_network(self):
        """启动网络"""
        target_dir = NETWORK_DIR
        if not target_dir.exists():
            raise ValueError(f"网络目录不存在: {target_dir}")
        
        cmd = [OPENAGENTS_EXE, "network", "start", str(target_dir)]
        log_file = self._get_log_path("network")
        proc = subprocess.Popen(
            cmd,
            cwd=str(target_dir), 
            stdout=open(log_file, "w", encoding='utf-8'),
            stderr=subprocess.STDOUT,
            env=ENV
        )
        self.processes["network"] = proc
        self.info.append({
            "type": "network",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(target_dir),
            "status": "running"
        })
    
    def start_agent(self, yaml_name: str):
        """启动 Agent (基于 YAML)"""
        yaml_file = SCRIPT_DIR / yaml_name
        if not yaml_file.exists():
            raise ValueError(f"Agent 配置不存在: {yaml_file}")
        
        cmd = [OPENAGENTS_EXE, "agent", "start", str(yaml_file)]
        log_file = self._get_log_path(f"agent_{yaml_file.stem}")
        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            stdout=open(log_file, "w", encoding='utf-8'),
            stderr=subprocess.STDOUT,
            env=ENV
        )
        self.processes[f"agent_{yaml_file.stem}"] = proc
        self.info.append({
            "type": "agent",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(SCRIPT_DIR),
            "status": "running"
        })
    
    def start_script(self, script_name: str):
        """运行 Python 脚本"""
        target_script = SCRIPT_DIR / script_name
        if not target_script.exists():
            raise ValueError(f"脚本不存在: {target_script}")
        
        cmd = [sys.executable, str(target_script)]
        log_file = self._get_log_path(f"script_{target_script.stem}")
        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR),
            stdout=open(log_file, "w", encoding='utf-8'),
            stderr=subprocess.STDOUT,
            env=ENV
        )
        self.processes[f"script_{target_script.stem}"] = proc
        self.info.append({
            "type": "script",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(SCRIPT_DIR),
            "status": "running"
        })
    
    def start_studio(self):
        """启动 Studio"""
        cmd = [OPENAGENTS_EXE, "studio", "-s"]
        log_file = self._get_log_path("studio")
        proc = subprocess.Popen(
            cmd,
            cwd=str(SCRIPT_DIR), 
            stdout=open(log_file, "w", encoding='utf-8'),
            stderr=subprocess.STDOUT,
            env=ENV
        )
        self.processes["studio"] = proc
        self.info.append({
            "type": "studio",
            "pid": proc.pid,
            "log": str(log_file),
            "cwd": str(SCRIPT_DIR),
            "status": "running"
        })
    
    def stop_all(self):
        """停止所有子进程"""
        for name, proc in self.processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except:
                try:
                    proc.kill()
                except:
                    pass
        self.processes.clear()
    
    def get_status_json(self):
        """返回状态信息"""
        return json.dumps(self.info, ensure_ascii=False, indent=2)

# ================= 主入口 =================
manager = ProcessManager()

def cleanup(signum=None, frame=None):
    """退出信号处理"""
    print("\n[Manager] 收到退出信号，正在清理所有子进程...")
    manager.stop_all()
    print("[Manager] 清理完毕。")
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python launcher.py <all|core|studio>")
        print("  all     - 启动 Network, 所有Agents (包括学生) 和 Studio")
        print("  core    - 启动 Network, 核心Agents (无学生) 和 Studio")
        print("  studio  - 仅启动 Studio")
        sys.exit(1)
    
    cmd_type = sys.argv[1]
    
    try:
        # 打印关键路径
        print(f"[Info] OpenAgents Executable: {OPENAGENTS_EXE}")
        print(f"[Info] Script Dir (Agents): {SCRIPT_DIR}")
        print(f"[Info] Network Dir (Parent): {NETWORK_DIR}")
        print(f"[Info] Log Dir: {LOG_DIR}")
        
        if cmd_type == "all":
            print("=" * 60)
            print("🚀 启动完整系统 - 包括旅行指南和哈利波特学院agents")
            print("=" * 60)
            
            # 1. 启动网络
            print("\n📡 [1/8] 启动网络...")
            manager.start_network()
            print(f"✅ Network 已启动 -> {NETWORK_DIR}")
            
            # 2. 启动 Travel Guide Agent
            print("\n🗺️  [2/8] 启动旅行指南 Agent...")
            manager.start_agent("travel-guide-agent.yaml")
            print(f"✅ Travel Guide Agent 已启动 -> travel-guide-agent.yaml")
            
            # 3. 启动 Weather Connector
            print("\n🌤️  [3/8] 启动天气连接器...")
            manager.start_script("weather_connector.py")
            print(f"✅ Weather Connector 已启动 -> weather_connector.py")
            
            # 4. 启动四个哈利波特学院学生agents
            print("\n🏰 [4/8] 启动哈利波特学院学生agents...")
            
            print("  🦁 格兰芬多学生...")
            manager.start_agent("gryffindor-student.yaml")
            print("  ✅ Gryffindor 学生已启动")
            
            print("  🐍 斯莱特林学生...")
            manager.start_agent("slytherin-student.yaml")
            print("  ✅ Slytherin 学生已启动")
            
            print("  🦅 拉文克劳学生...")
            manager.start_agent("ravenclaw-student.yaml")
            print("  ✅ Ravenclaw 学生已启动")
            
            print("  🦡 赫奇帕奇学生...")
            manager.start_agent("hufflepuff-student.yaml")
            print("  ✅ Hufflepuff 学生已启动")
            
            # 5. 启动 Studio
            print("\n🎨 [8/8] 启动 Studio...")
            manager.start_studio()
            print(f"✅ Studio 已启动")
            
            print("\n" + "=" * 60)
            print("🎉 所有Agents已启动！系统正在守护中...")
            print("=" * 60)
            print("\n📝 使用方式:")
            print("  • 使用 travel_sender.py 发送旅游指南请求")
            print("  • 四个学院学生将根据各自的特质提供旅行建议")
            print("  • Studio 可视化界面: http://localhost:xxxx")
            print("\n🏰 哈利波特学院特质:")
            print("  🦁 格兰芬多: 勇敢冒险，面对挑战")
            print("  🐍 斯莱特林: 战略规划，高效优雅")
            print("  🦅 拉文克劳: 学习成长，文化探索")
            print("  🦡 赫奇帕奇: 温馨安全，友善包容")
            print("\n按 Ctrl+C 停止所有服务")
            print("=" * 60)

        elif cmd_type == "core":
            print("=" * 60)
            print("🚀 启动核心系统 - 仅包括旅行指南Agent和天气连接器")
            print("=" * 60)
            
            # 1. 启动网络
            print("\n📡 [1/4] 启动网络...")
            manager.start_network()
            print(f"✅ Network 已启动 -> {NETWORK_DIR}")
            
            # 2. 启动 Travel Guide Agent
            print("\n🗺️  [2/4] 启动旅行指南 Agent...")
            manager.start_agent("travel-guide-agent.yaml")
            print(f"✅ Travel Guide Agent 已启动 -> travel-guide-agent.yaml")
            
            # 3. 启动 Weather Connector
            print("\n🌤️  [3/4] 启动天气连接器...")
            manager.start_script("weather_connector.py")
            print(f"✅ Weather Connector 已启动 -> weather_connector.py")
            
            # 4. 启动 Studio
            print("\n🎨 [4/4] 启动 Studio...")
            manager.start_studio()
            print(f"✅ Studio 已启动")
            
            print("\n" + "=" * 60)
            print("🎉 核心系统已启动！")
            print("=" * 60)
            print("\n📝 使用方式:")
            print("  • 使用 travel_sender.py 发送旅游指南请求")
            print("  • Studio 可视化界面: http://localhost:xxxx")
            print("  • 注意: 学院学生Agents未启动")
            print("\n按 Ctrl+C 停止所有服务")
            print("=" * 60)
            
        elif cmd_type == "studio":
            print("-" * 40)
            manager.start_studio()
            print(f"[Action] 已启动 Studio")
            print("-" * 40)
            print("[Manager] Studio 已启动，守护中...")
        else:
            print(f"未知命令: {cmd_type}，目前支持 'all', 'core', 'studio'")
            sys.exit(1)
        
        # 输出状态给 Tauri
        print("<<<START_INFO>>>")
        print(manager.get_status_json())
        print("<<<END_INFO>>>")
        
        # 保持挂起
        while True:
            pass
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("<<<START_INFO>>>")
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        print("<<<END_INFO>>>")
        sys.exit(1)

