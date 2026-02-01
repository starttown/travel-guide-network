<script lang="ts">
  import { onMount } from 'svelte';
  import { invoke } from "@tauri-apps/api/core";
  import { listen } from "@tauri-apps/api/event";

  let city = $state("Beijing");
  let dateOffset = $state(0);
  let senderResult = $state("");
  let serverLogs: string[] = $state([]);

  function escapeHtml(unsafe: unknown): string {
    const str = String(unsafe);
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  async function callService(event: Event) {
    event.preventDefault();
    senderResult = "Calling Python backend...";

    try {
      const res = await invoke<string>("call_service", {
        city,
        dateOffset,
      });
      senderResult = `Status: success\nResponse: ${res}`;
    } catch (e: any) {
      console.error("call_service error:", e);
      senderResult = `Error: ${String(e)}`;
    }
  }

  onMount(async () => {
    const unlisten = await listen<string>("log-line", (event) => {
      const logMsg = event.payload;
      if (serverLogs.length > 500) {
        serverLogs = serverLogs.slice(-400);
      }
      serverLogs = [...serverLogs, logMsg];
    });

    return () => {
      unlisten();
    };
  });

  function clearLogs() {
    serverLogs = [];
  }

   function exportToPDF() {
    if (serverLogs.length === 0) {
      alert("当前没有日志可打印");
      return;
    }

    // 生成 HTML 内容（只保留日志，去掉了标题和时间戳）
    const logsHtml = serverLogs
      .map(
        (log) =>
          `<div style="margin-bottom: 16px; border-bottom: 1px dashed #ccc; padding-bottom: 8px;">
             <pre style="font-family: monospace; white-space: pre-wrap; margin: 0; font-size: 12px; color: #000;">${escapeHtml(
            log
          )}</pre>
           </div>`
      )
      .join("");

    // 写入隐藏的打印区域
    const printArea = document.getElementById("print-area");
    if (printArea) {
      // 直接只放入日志内容
      printArea.innerHTML = logsHtml;

      // 延迟打印
      setTimeout(() => {
        window.print();
        
        // 打印后清空
        setTimeout(() => {
           printArea.innerHTML = "";
        }, 1000);
      }, 300);
    }
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
          onclick={exportToPDF}
          class="rounded-lg border border-sky-200 px-3 py-2 text-sm text-sky-700 hover:bg-sky-50 transition"
        >
          Export Guides PDF
        </button>

        <button
          onclick={clearLogs}
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

        <form id="plan-form" onsubmit={callService} class="space-y-4">
          <div>
            <label for="city" class="block text-sm font-medium text-slate-700 mb-1">City (Eng)</label>
            <input
              id="city"
              name="city"
              type="text"
              bind:value={city}
              placeholder="e.g. London"
              required
              class="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </div>

          <div>
            <label for="date" class="block text-sm font-medium text-slate-700 mb-1">Date Offset (days)</label>
            <div class="flex items-center gap-2">
              <input
                id="date"
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
          {#if senderResult}
            {senderResult}
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

  <!-- 隐藏的打印区域，只有在打印时会显示 -->
  <div id="print-area" style="display: none;"></div>
</div>
