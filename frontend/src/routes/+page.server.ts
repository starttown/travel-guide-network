import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';

// 页面加载时的服务端逻辑（当前为空）
export const load: PageServerLoad = async () => {
	return {};
};

// 定义页面的服务端 Actions（处理表单提交）
export const actions: Actions = {
	// 这里的 'callService' 对应前端 form action="?/callService"
	callService: async ({ request }) => {
		// 1. 获取前端表单提交的数据
		const formData = await request.formData();
		const city = formData.get('city');
		const dateStr = formData.get('date'); 

		// 2. 基础校验：确保必填项不为空
		if (!city || !dateStr) {
			// fail(400, ...) 会返回 400 错误，并携带 error 信息给前端 form.error
			return fail(400, { error: '城市和日期偏移量不能为空' });
		}

		// 3. 数据转换：将日期字符串转换为整数
		const dateNum = parseInt(dateStr as string, 10);

		// 校验转换后的数字是否有效
		if (isNaN(dateNum)) {
			return fail(400, { error: '日期必须是数字' });
		}

		// 4. 构建发送给 Python 服务 (8888端口) 的 JSON 数据包
		const payload = {
			city: city,     // 保持为字符串
			date: dateNum   // 转为数字
		};

		try {
			// 打印日志，方便在服务端控制台查看请求内容
			console.log(`[Client] Sending to 8888:`, JSON.stringify(payload));

			// 5. 发起 HTTP 请求，调用 Python 服务
			const resp = await fetch('http://localhost:8888/generate', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			});

			// 获取 Python 服务返回的文本内容
			const text = await resp.text();

			// 6. 返回成功结果给前端 (填充 form.output)
			return {
				success: true,
				output: `Status: ${resp.status}\nResponse: ${text}`
			};

		} catch (e: any) {
			// 7. 异常处理：如果连接失败或报错，返回 500 错误给前端
			console.error('连接 8888 失败:', e);
			return fail(500, { error: `Error: ${e.message}` });
		}
	}
};
