import sys
import os
import subprocess
import signal
import time
import platform
from pathlib import Path
import socket

# ================= UTF-8 强制设置 =================
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ENV = os.environ.copy()
ENV["PYTHONIOENCODING"] = "utf-8"
ENV["PYTHONUTF8"] = "1"

# ================= 路径与常量定义 =================
ROOT_DIR = Path(__file__).parent.resolve()
NETWORK_DIR = ROOT_DIR / "network"
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_PORT = 8888
LOCAL_NODE_DIR = ROOT_DIR / "nodejs"  # 定义本地 Node.js 目录

if not NETWORK_DIR.exists():
    raise FileNotFoundError(f"后端目录不存在: {NETWORK_DIR}")
if not FRONTEND_DIR.exists():
    raise FileNotFoundError(f"前端目录不存在: {FRONTEND_DIR}")

# ================= 进程管理类 =================
class ProcessManager:
    """负责同时启动和管理前端、后端进程"""

    def __init__(self):
        self.processes = {}

    def _wait_for_port(self, port: int, host: str = '127.0.0.1', timeout: int = 60):
        """等待指定端口开启"""
        start_time = time.time()
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex((host, port)) == 0:
                        print(f"✅ [Backend] 端口 {port} 已就绪")
                        return True
            except Exception:
                pass
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"等待后端启动超时（{timeout}秒），端口 {port} 未开启")
            time.sleep(1)

    def _run_command(self, name, cmd, cwd, shell=False):
        """启动子进程并实时输出日志"""
        print(f"🚀 [{name}] 正在启动...")
        print(f"    目录: {cwd}")
        
        is_windows = platform.system() == "Windows"
        # Windows 下默认使用 shell，否则无法找到 .cmd 文件或正确处理路径
        use_shell = shell or is_windows

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                env=ENV,
                shell=use_shell,
                stdout=sys.stdout,
                stderr=sys.stderr,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_windows else 0
            )
            self.processes[name] = proc
            print(f"✅ [{name}] 进程已启动 (PID: {proc.pid})\n")
            return proc
        except Exception as e:
            print(f"❌ [{name}] 启动失败: {e}\n")
            raise

    def start_backend(self, wait_port=None):
        """启动后端"""
        launch_file = NETWORK_DIR / "launch.py"
        if not launch_file.exists():
            raise FileNotFoundError(f"找不到 launch.py: {launch_file}")

        # Windows 下使用 sys.executable 即可，打包后就是相对路径的 python.exe
        cmd = [sys.executable, "launch.py", "all"]
        self._run_command("Backend", cmd, cwd=NETWORK_DIR)

        if wait_port:
            print(f"⏳ [Backend] 正在等待服务启动 (端口: {wait_port})...")
            self._wait_for_port(wait_port)

    def start_frontend(self):
        """启动前端"""
        is_windows = platform.system() == "Windows"
        cmd = []

        if is_windows:
            # Windows: 使用相对路径下的 pnpm
            pnpm_path = LOCAL_NODE_DIR / "pnpm.cmd"
            
            if not pnpm_path.exists():
                print(f"❌ [Frontend] 错误：找不到本地 pnpm ({pnpm_path})")
                print("   请确保打包时已包含 nodejs 目录并安装了 pnpm。")
                sys.exit(1)
            
            cmd = [str(pnpm_path.resolve()), "dev", "--host", "--open"]
            print(f"🔍 [Frontend] 使用本地环境: {cmd[0]}")
        else:
            # Ubuntu/Linux: 直接使用系统的 pnpm
            cmd = ["pnpm", "dev", "--host", "--open"]
            print(f"🔍 [Frontend] 使用系统环境 pnpm")

        # _run_command 内部会自动处理 Windows 的 shell=True 逻辑
        self._run_command("Frontend", cmd, cwd=FRONTEND_DIR)

    def stop_all(self):
        """停止所有子进程"""
        print("\n🛑 正在停止所有服务...")
        for name, proc in self.processes.items():
            try:
                if platform.system() == "Windows":
                    subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception as e:
                print(f"   停止 {name} 时出错: {e}")
        
        self.processes.clear()
        print("✅ 所有服务已停止。")

# ================= 全局管理器 =================
manager = ProcessManager()

# ================= 退出信号处理 =================
def cleanup(signum=None, frame=None):
    if not manager.processes:
        sys.exit(0)
    manager.stop_all()
    sys.exit(0)

def register_signals():
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, cleanup)
        signal.signal(signal.SIGINT, cleanup)
    else:
        signal.signal(signal.SIGINT, cleanup)

# ================= 主入口 =================
def main():
    register_signals()

    print("=" * 70)
    print("🚀 正在启动 Travel Guide Network System")
    print("=" * 70)

    try:
        # 1. 启动后端并阻塞等待端口 8888
        manager.start_backend(wait_port=BACKEND_PORT)

        # 2. 启动前端
        manager.start_frontend()

        print("=" * 70)
        print("🎉 系统启动完成！")
        print("=" * 70)
        print("提示: 按 Ctrl+C 可随时停止所有服务")
        print("=" * 70)

        while True:
            for name, proc in list(manager.processes.items()):
                if proc.poll() is not None:
                    print(f"⚠️  检测到 [{name}] 意外退出，正在停止所有服务...")
                    manager.stop_all()
                    sys.exit(1)
            time.sleep(1)

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"\n❌ 发生错误: {e}", file=sys.stderr)
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()
