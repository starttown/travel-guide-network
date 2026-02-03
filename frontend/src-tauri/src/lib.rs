use serde::Deserialize;
//use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager, State};
use std::env; 
// ============ 命令参数定义 ============

#[derive(Deserialize)]
pub struct LogPayload {
    #[serde(default)]
    pub agent: String,
    #[serde(default)]
    pub content: String,
}

// ============ 调用 Python 后端的命令 ============

#[tauri::command]
async fn call_service(
    city: String,
    // 修复点：允许参数使用 camelCase，以便直接匹配前端 JSON 键名
    #[allow(non_snake_case)] dateOffset: i32,
) -> Result<String, String> {
    let payload = serde_json::json!({
        "city": city,
        "date": dateOffset,
    });

    println!("[Client] Sending to 8888: {}", payload);

    let client = reqwest::Client::new();

    let resp: reqwest::Response = client
        .post("http://localhost:8888/generate")
        .header("Content-Type", "application/json")
        .json(&payload)
        .send()
        .await
        .map_err(|e| format!("连接 Python backend 失败: {}", e))?;

    let status = resp.status();
    let body = resp
        .text()
        .await
        .map_err(|e| format!("读取响应失败: {}", e))?;

    Ok(format!("Status: {}\nResponse: {}", status, body))
}

// ============ 启动内部 Log Server 的核心逻辑 ============

fn start_log_server_impl(app: AppHandle, started_flag: Arc<Mutex<bool>>) {
    {
        let mut started = started_flag.lock().unwrap();
        if *started {
            println!("[Log Server] 已经在运行中，跳过启动");
            return;
        }
        *started = true;
    }

    std::thread::spawn(move || {
        let server = tiny_http::Server::http("127.0.0.1:9999").expect("无法启动 Log Server");
        println!("🚀 [Log Server] 已启动监听端口 9999");

        for request in server.incoming_requests() {
            let mut request: tiny_http::Request = request;

            if request.method() != &tiny_http::Method::Post || request.url() != "/log" {
                let _ = request.respond(
                    tiny_http::Response::from_string("Not Found".to_string())
                        .with_status_code(tiny_http::StatusCode(404)),
                );
                continue;
            }

            let mut body = Vec::new();
            if std::io::Read::read_to_end(&mut request.as_reader(), &mut body).is_err() {
                continue;
            }

            let body_str = match std::str::from_utf8(&body) {
                Ok(s) => s,
                Err(_) => continue,
            };

            if body_str.trim().is_empty() {
                let _ = request.respond(
                    tiny_http::Response::from_string("OK".to_string())
                        .with_status_code(tiny_http::StatusCode(200)),
                );
                continue;
            }

            let data: LogPayload = match serde_json::from_str(body_str) {
                Ok(d) => d,
                Err(_) => continue,
            };

            let agent = if data.agent.is_empty() {
                "Unknown".to_string()
            } else {
                data.agent
            };

            let time = chrono::Local::now().format("%H:%M:%S").to_string();
            let log_text = format!(
                "\n{}\n📩 [{}] 收到来自 '{}' 的消息:\n{}\n{}\n",
                "=".repeat(70),
                time,
                agent,
                data.content,
                "=".repeat(70)
            );

            println!("{}", log_text);

            // 推送到前端
            let _ = app.emit("log-line", &log_text);

            // // 2. 修改文件路径逻辑，确保写入 src-tauri 外面
            // // CARGO_MANIFEST_DIR 指向 src-tauri 目录
            // let base_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
            // // project_root = src-tauri 的上一级目录 (项目根目录)
            // let project_root = base_dir.join("..");
            // let log_dir = project_root.join("logs");
            
            // let _ = std::fs::create_dir_all(&log_dir);
            // let log_file = log_dir.join("agent-logs.txt");
            
            // let _ = std::fs::OpenOptions::new()
            //     .create(true)
            //     .append(true)
            //     .open(&log_file)
            //     .and_then(|mut file| std::io::Write::write_all(&mut file, log_text.as_bytes()));

            let _ = request.respond(
                tiny_http::Response::from_string(
                    serde_json::json!({ "status": "received" }).to_string(),
                )
                .with_status_code(tiny_http::StatusCode(200))
                .with_header(
                    tiny_http::Header::from_bytes(&b"Content-Type"[..], &b"application/json"[..])
                        .unwrap(),
                ),
            );
        }
    });
}

// ============ 暴露给 Tauri 的命令 ============

#[tauri::command]
fn start_log_server(app: AppHandle, state: State<'_, Arc<Mutex<bool>>>) -> Result<(), String> {
    let flag = (*state).clone();
    start_log_server_impl(app, flag);
    Ok(())
}

// ============ 应用入口 ============

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let started_flag = Arc::new(Mutex::new(false));

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_opener::init())
        .manage(started_flag)
        .setup(|app| {
            let app_handle = app.handle().clone();
            let state = app.state::<Arc<Mutex<bool>>>();
            let flag = (*state).clone();

            tauri::async_runtime::spawn(async move {
                start_log_server_impl(app_handle, flag);
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![call_service, start_log_server,])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
