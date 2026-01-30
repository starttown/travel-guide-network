<script lang="ts">
  import { onMount } from 'svelte';
  import { enhance } from '$app/forms';
  import type { ActionData } from './$types';

  export let form: ActionData;

  let city = 'Beijing';
  let dateOffset = 0;

  let serverLogs: string[] = [];
  let eventSource: EventSource;

  // 工具函数：防止 XSS 攻击，转义 HTML 特殊字符
  function escapeHtml(unsafe: unknown): string {
    const str = String(unsafe);
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  onMount(() => {
    eventSource = new EventSource('/api/stream');
    
    // 新增：错误处理，防止连接静默失败
    eventSource.onerror = (err) => {
      console.error('SSE Connection Error:', err);
      // 如果需要断开后不再自动重连，可在此处调用 eventSource.close()
    };

    eventSource.onmessage = (event) => {
      try {
        // 尝试解析 JSON
        const logMsg = JSON.parse(event.data);
        
        // 修复：限制日志长度，防止内存溢出
        if (serverLogs.length > 500) {
          serverLogs = serverLogs.slice(-400); // 保留最近的 400 条
        }
        
        serverLogs = [...serverLogs, logMsg];
      } catch (e) {
        // 修复：JSON 解析失败时，将原始数据作为字符串记录，防止中断
        console.warn('Failed to parse log message', e);
        serverLogs = [...serverLogs, event.data];
      }
    };
    
    return () => eventSource.close();
  });

  function clearLogs() {
    serverLogs = [];
  }

  function exportToPDF() {
    if (serverLogs.length === 0) {
      alert("当前没有日志可打印");
      return;
    }

    const now = new Date();
    const timestamp = now.getFullYear() +
      '-' + String(now.getMonth() + 1).padStart(2, '0') +
      '-' + String(now.getDate()).padStart(2, '0') +
      '_' + String(now.getHours()).padStart(2, '0') +
      '-' + String(now.getMinutes()).padStart(2, '0') +
      '-' + String(now.getSeconds()).padStart(2, '0');

    const fileName = `Travel_Guides_${timestamp}`;

    const printWindow = window.open('', '', 'width=800,height=600');
    if (!printWindow) return;

    // 修复：使用 escapeHtml 防止 XSS
    const logsHtml = serverLogs
      .map(log => `<pre style="font-family: monospace; white-space: pre-wrap; margin-bottom: 8px;">${escapeHtml(log)}</pre>`)
      .join('');

    printWindow.document.write(`
      <html>
        <head>
          <title>${fileName}</title>
          <style>
            body { font-family: sans-serif; padding: 20px; color: #000; background: #fff; }
            h2 { border-bottom: 1px solid #ccc; padding-bottom: 10px; }
          </style>
        </head>
        <body>
          <h2>Travel Guides (Generated: ${timestamp})</h2>
          <div>${logsHtml}</div>
        </body>
      </html>
    `);
    printWindow.document.close();

    printWindow.focus();
    printWindow.print();
  }
</script>

<div class="min-h-screen bg-gradient-to-b from-sky-50 to-white text-slate-800">
  <header class="border-b border-sky-200 bg-white/80 backdrop-blur sticky top-0 z-10">
    <div class="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
      <h1 class="text-xl sm:text-2xl font-semibold text-sky-900 tracking-tight flex items-center gap-2">
        <span>✈️</span> Travel-Guide-NetWork
      </h1>

      <div class="flex items-center gap-3">
        <button
          type="submit"
          form="plan-form"
          class="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-sky-500 transition"
        >
          Generate Travel Guides
        </button>
        
        <button
          on:click={exportToPDF}
          class="rounded-lg border border-sky-200 px-3 py-2 text-sm text-sky-700 hover:bg-sky-50 transition"
        >
          Export Guides PDF
        </button>

        <button
          on:click={clearLogs}
          class="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-600 hover:bg-red-50 transition"
        >
          Clear Guides
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-6">
    <section class="grid gap-6 md:grid-cols-2">
      <div class="rounded-2xl border border-sky-200 bg-white p-5 shadow-sm">
        <h2 class="text-base font-semibold text-sky-900 mb-4 flex items-center gap-2">
          <span>📡</span> Travel Sender
        </h2>

        <form id="plan-form" method="POST" action="?/callService" use:enhance class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">City (Eng)</label>
            <input
              name="city"
              type="text"
              bind:value={city}
              placeholder="e.g. London"
              required
              class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Date Offset (days)</label>
            <div class="flex items-center gap-2">
              <input
                name="date"
                type="number"
                bind:value={dateOffset}
                min="-30"
                max="15"
                step="1"
                required
                class="w-full max-[140px] rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
              <span class="text-xs text-slate-500">{dateOffset > 0 ? '+' : ''}{dateOffset} days</span>
            </div>
          </div>
        </form>
      </div>

      <div class="rounded-2xl border border-sky-200 bg-white p-5 shadow-sm flex flex-col">
        <h2 class="text-base font-semibold text-sky-900 mb-3 flex items-center gap-2">
          <span>📋</span> Sender Result
        </h2>

        <pre
          class="flex-1 min-h-[120px] rounded-md bg-slate-900 text-emerald-400 text-xs p-3 overflow-auto font-mono"
        >
          {#if form?.output}
            {form.output}
          {:else if form?.error}
            <span class="text-red-400">{form.error}</span>
          {:else}
            ...
          {/if}
        </pre>
      </div>
    </section>

    <section class="rounded-2xl border border-sky-200 bg-white p-5 shadow-sm">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-base font-semibold text-sky-900 flex items-center gap-2">
          <span>📩</span> Travel Guides
        </h2>
      </div>

      <div class="rounded-md bg-slate-900 text-emerald-400 text-xs p-3 min-h-[240px] overflow-auto font-mono space-y-1">
        {#each serverLogs as log}
          <pre>{log}</pre>
        {/each}
        {#if serverLogs.length === 0}
          <p class="text-slate-500 italic">...</p>
        {/if}
      </div>
    </section>
  </main>
</div>
