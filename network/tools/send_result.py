import requests
import json

def send_result_to_server(agent_id: str, content: str) -> str:
    """
    将 Agent 的建议通过 HTTP POST 发送到日志服务器。
    
    Args:
        agent_id: 发送者的 ID (e.g., "gryffindor-student")
        content: 要发送的建议文本内容
    
    Returns:
        操作结果字符串
    """
    server_url = "http://localhost:9999/log"
    
    payload = {
        "agent": agent_id,
        "content": content,
        "timestamp": "" # 可选，由服务器处理
    }

    try:
        # 设置超时，防止长时间阻塞
        resp = requests.post(server_url, json=payload, timeout=5)
        
        if resp.status_code == 200:
            print(f"✅ [{agent_id}] 成功发送建议到服务器")
            return "Successfully sent to log server"
        else:
            print(f"⚠️ [{agent_id}] 服务器响应错误: {resp.status_code}")
            return f"Server responded with status {resp.status_code}"
            
    except requests.exceptions.ConnectionError:
        error_msg = "Connection refused: Is the log server running?"
        print(f"❌ [{agent_id}] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send: {str(e)}"
        print(f"❌ [{agent_id}] {error_msg}")
        return error_msg
