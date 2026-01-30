# TravelGuide Frontend Dashboard
The web-based user interface for the TravelGuide Multi-Agent System. Built with **SvelteKit** and **Tailwind CSS**, this dashboard provides real-time monitoring and control over the backend Python agents.
## 📋 Project Overview
This application serves as the control center for the travel recommendation system. It allows users to submit travel requests and view real-time logs streamed directly from the Python backend agents via Server-Sent Events (SSE).
**Key Integration:** The Node.js server (running this SvelteKit app) also hosts an internal Log Server on port `9999` that receives updates from the Python backend and forwards them to the browser.
## ✨ Features
-   **📡 Travel Request Form**: Submit city and date parameters to trigger the backend workflow.
-   **📩 Real-time Logs**: View agent output (Gryffindor, Slytherin, Ravenclaw, Hufflepuff) instantly as they are generated via SSE.
-   **🛡️ XSS Protection**: Built-in HTML sanitization to safely display logs and prevent injection attacks.
-   **📄 PDF Export**: Export the generated travel guides to PDF directly from the browser.
-   **🎨 Modern UI**: Responsive design built with Tailwind CSS.
-   **⚡ Optimistic UI**: Fast interactions using SvelteKit form actions.
## 🛠️ Tech Stack
-   **Framework**: [SvelteKit](https://kit.svelte.dev/) (with SSR disabled for client-side streaming)
-   **Styling**: [Tailwind CSS](https://tailwindcss.com/)
-   **Build Tool**: Vite
-   **Streaming**: Server-Sent Events (SSE) via custom Vite plugin
-   **Package Manager**: [pnpm](https://pnpm.io/)
-   **Backend Dependency**: Python Weather Connector (must be running on `localhost:8888`)
## 🚀 Getting Started
### Prerequisites
1.  **Node.js**: Version 16+ or 18+ installed.
2.  **pnpm**: Fast, disk space efficient package manager.
    ```bash
    npm install -g pnpm
    # or enable corepack: corepack enable
    ```
3.  **Python Backend**: The `weather_connector.py` service must be running on `http://localhost:8888`.
4.  **Network**: The application currently targets `localhost`. If deploying remotely, API URLs in `+page.server.ts` and Python scripts need adjustment.
### Installation
1.  Clone the repository and navigate to the frontend directory:
    ```bash
    cd /path/to/frontend
    ```
2.  Install dependencies using pnpm:
    ```bash
    pnpm install
    ```
### Development Mode
Run the development server. By default, it runs on `http://localhost:5173`.
```bash
pnpm dev --host --open
```
> **Note:** The development server automatically starts the **Internal Log Server** on port `9999`. Ensure no other service is using this port.

## 📂 Project Structure
```
.
├── src/
│   ├── routes/
│   │   └── +page.svelte         # Main UI component (Form + Log Viewer)
│   │   ├── +page.server.ts      # Server actions (Handle form submit -> Call Python)
│   │   └── +server.ts           # SSE Endpoint (Stream logs to browser)
│   ├── app.html                 # HTML template
│   └── app.css                  # Tailwind imports
├── static/                      # Static assets
├── vite.config.ts               # Vite config + Custom Log Server Plugin
├── svelte.config.js             # SvelteKit adapter config
├── package.json                 # Project metadata
└── pnpm-lock.yaml               # pnpm lockfile
```
## 🏗️ Architecture & Data Flow
This application utilizes a unique 3-way communication pattern:
1.  **User Action**: User fills the form in `+page.svelte`.
    *   Data is sent via POST to SvelteKit Server Action (`+page.server.ts`).
2.  **Backend Trigger**: `+page.server.ts` forwards the request to Python Backend (`http://localhost:8888/generate`).
3.  **Agent Processing**: Python backend delegates tasks to Agents.
4.  **Log Relay**: Agents send results to the **Internal Log Server** embedded in this Node app (`http://localhost:9999/log`).
    *   *Implementation:* This is handled by the custom `log-server-9999` plugin in `vite.config.ts`.
5.  **Real-time Push**: The Log Server emits an event. The `+server.ts` SSE endpoint catches this event and pushes it to the browser.
6.  **UI Update**: The browser (`+page.svelte`) receives the SSE message and updates the log list.
## ⚙️ Configuration
### Ports
-   **Frontend (Dev)**: `5173`
-   **Frontend (Prod)**: `3000` (or configured port)
-   **Internal Log Server**: `9999` (Hardcoded in `vite.config.ts`)
-   **Python Backend**: `8888` (Hardcoded in `+page.server.ts`)
### Tailwind CSS
Tailwind is configured via the Vite plugin. No additional config file (`tailwind.config.js`) is required as the default configuration is used.
## 🔒 Security Features
-   **XSS Prevention**: The `escapeHtml` function in `+page.svelte` sanitizes all log data before rendering it to the DOM, mitigating Cross-Site Scripting risks from potentially malicious agent outputs.
-   **Input Validation**: Server-side validation in `+page.server.ts` ensures only valid data reaches the Python backend.
## 🐛 Troubleshooting
### "Connection refused" when submitting form
-   **Cause**: The Python backend (`weather_connector.py`) is not running.
-   **Fix**: Ensure `python launch.py all` or the specific connector script is running.
### Logs not appearing
-   **Cause 1**: The Python `send_result.py` is pointing to the wrong URL. It must point to `http://localhost:9999/log`.
-   **Cause 2**: Port `9999` is blocked or occupied by another application.
-   **Fix**: Check the console where `pnpm dev` is running to ensure `🚀 [Log Server] 已启动监听端口 9999` appears.
### PDF Export fails
-   **Cause**: Browser popup blocker.
-   **Fix**: Allow popups for this site.
## 📄 License
This project is open source and available under the [MIT License](https://choosealicense.com/licenses/mit/).
---
**Developed with ❤️ using SvelteKit**
