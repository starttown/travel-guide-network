import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	let closed = false;
	const encoder = new TextEncoder(); // 字符编码器，用于将字符串转为二进制流

	const stream = new ReadableStream({
		start(controller) {
			// 1. 获取全局挂载的日志发布器
			const emitter = (globalThis as any).SvelteKitLogEmitter;

			// 2. 严格校验：确保 emitter 存在且具备 subscribe 方法
			if (!emitter || typeof emitter.subscribe !== 'function') {
				controller.close();
				return;
			}

			// 3. 订阅日志事件：每次 emitter 发布数据时，触发此回调
			const unsubscribe = emitter.subscribe((data: unknown) => {
				// 安全检查：若流已关闭，停止处理
				if (closed) return;

				try {
					// 4. 格式化数据：按照 SSE 协议要求，封装为 `data: <json>\n\n`
					// JSON.stringify 确保数据结构安全转义
					const sseMessage = `data: ${JSON.stringify(data)}\n\n`;
					
					// 5. 编码转换：将字符串转为 Uint8Array
					const chunk = encoder.encode(sseMessage);

					// 6. 入队发送：将二进制数据块推入 HTTP 响应流，前端即刻收到
					controller.enqueue(chunk);
				} catch (e) {
					// 7. 异常熔断：发生错误时（如序列化失败），必须关闭流并移除订阅
					closed = true;
					unsubscribe();
					controller.close();
				}
			});

			// 8. 清理函数：当流被取消（如用户关闭页面）时自动执行
			return () => {
				closed = true;
				unsubscribe();
			};
		},
		cancel() {
			closed = true;
		}
	});

	return new Response(stream, {
		headers: {
			'Content-Type': 'text/event-stream',
			'Cache-Control': 'no-cache',
			'Connection': 'keep-alive',
			'X-Accel-Buffering': 'no' // 禁用 Nginx 缓冲，确保 SSE 实时性
		}
	});
};
