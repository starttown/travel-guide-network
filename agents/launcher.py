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
    """解析 openagents.exe 的路径。"""
    python_dir = Path(sys.executable).parent.resolve()
    
    # 尝试 1: 与 python.exe 同级
    oa_path = python_dir / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)
    
    # 尝试 2: Scripts 文件夹下
    oa_path = python_dir / "Scripts" / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)
    
    # 尝试 3: 上一级
    oa_path = python_dir.parent / "openagents.exe"
    if oa_path.exists():
        return str(oa_path)
    
    raise FileNotFoundError(
        f"找不到 openagents.exe。\n"
        f"已在以下位置搜索:\n"
        f"1. {python_dir}\n"
        f"2. {python_dir / 'Scripts'}\n"
        f"请确认 openagents.exe 是否已安装。"
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
            creationflags=subprocess.CREATE_NO_WINDOW,
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
            creationflags=subprocess.CREATE_NO_WINDOW,
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
            creationflags=subprocess.CREATE_NO_WINDOW,
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
            creationflags=subprocess.CREATE_NO_WINDOW,
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
        print("Usage: python launcher.py <all|studio>")
        print("  all     - 启动 Network, Connector, Agent 和 Studio")
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
            print("-" * 40)
            # 1. 启动网络
            manager.start_network()
            print(f"[Action] 已启动 Network -> {NETWORK_DIR}")
            
            # 2. 启动 Travel Guide Agent (YAML)
            manager.start_agent("travel-guide-agent.yaml")
            print(f"[Action] 已启动 Agent -> travel-guide-agent.yaml")
            
            # 3. 启动 Weather Connector (Python)
            manager.start_script("weather_connector.py")
            print(f"[Action] 已启动 Script -> weather_connector.py")
            
            # 4. 启动 Studio
            manager.start_studio()
            print(f"[Action] 已启动 Studio")
            
            print("-" * 40)
            print("[Manager] 所有程序已启动，守护中...")
            print("[Manager] 使用 travel_sender.py 发送旅游指南请求")
            
        elif cmd_type == "studio":
            print("-" * 40)
            manager.start_studio()
            print(f"[Action] 已启动 Studio")
            print("-" * 40)
            print("[Manager] Studio 已启动，守护中...")
        else:
            print(f"未知命令: {cmd_type}，目前支持 'all', 'studio'")
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
