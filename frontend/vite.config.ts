import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite'
import { createServer as createHttpServer } from 'http';
import fs from 'fs'; // 使用 ES Module import
import path from 'path'; // 使用 ES Module import

// 日志事件发射器
const logEmitter = {
	listeners: [] as ((data: string) => void)[],
	subscribe(callback: (data: string) => void) {
		this.listeners.push(callback);
		return () => {
			this.listeners = this.listeners.filter(cb => cb !== callback);
		};
	},
	emit(data: string) {
		this.listeners.forEach(cb => cb(data));
	}
};

// 挂载全局供 API 使用
(globalThis as any).SvelteKitLogEmitter = logEmitter;

export default defineConfig({
	plugins: [
	      sveltekit(),
	      tailwindcss(),
		{
			name: 'log-server-9999',
			configureServer() {
				// 定义日志目录和文件路径
				const logDir = path.resolve(process.cwd(), 'logs');
				const logFile = path.join(logDir, 'agent-logs.txt');

				// 启动前确保目录存在
				if (!fs.existsSync(logDir)) {
					fs.mkdirSync(logDir);
				}

				const logServer = createHttpServer((req, res) => {
					if (req.method === 'POST' && req.url === '/log') {
						let body = '';

						req.on('data', (chunk) => {
							body += chunk;
						});

						req.on('end', () => {
							// 1. 处理空 Body
							if (!body || body.trim() === '') {
								res.writeHead(200);
								res.end('OK');
								return;
							}

							try {
								// 2. 解析 JSON
								const data = JSON.parse(body.trim());
								const agent = data.agent || 'Unknown';
								const content = data.content || '';
								const time = new Date().toLocaleTimeString();

								// 3. 格式化日志
								const logText = `\n${'='.repeat(70)}\n📩 [${time}] 收到来自 '${agent}' 的消息:\n${'='.repeat(70)}\n${content}\n${'='.repeat(70)}\n`;

								// 4. 打印到控制台
								console.log(logText);

								// 5. 推送给前端
								logEmitter.emit(logText);

								// 6. 写入文件 (现在 fs 是通过 import 引入的，不会报错了)
								fs.appendFileSync(logFile, logText);

								// 7. 响应成功
								res.writeHead(200, { 'Content-Type': 'application/json' });
								res.end(JSON.stringify({ status: 'received' }));

							} catch (e) {
								// 捕获错误
								console.error('❌ [Server] 处理请求失败:', e);
								res.writeHead(200, { 'Content-Type': 'application/json' }); // 依然返回 200 防止对方崩溃
								res.end(JSON.stringify({ error: 'Server Error' }));
							}
						});
					} else {
						res.writeHead(404);
						res.end('Not Found');
					}
				});

				logServer.listen(9999, () => {
					console.log('🚀 [Log Server] 已启动监听端口 9999');
					console.log(`📂 [Log Server] 日志将保存至: ${logFile}`);
				});
			}
		}
	]
});
