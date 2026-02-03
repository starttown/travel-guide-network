# Travel-Guide-Network
A cross-platform desktop application built with **Tauri** + **SvelteKit** + **Tailwind CSS**. This app serves as the frontend interface, interacting with a Python backend service to generate and manage travel guides.
It integrates real-time log streaming, custom print-to-PDF export, and cross-language communication capabilities.
## ✨ Features
- 🚀 **Cross-Platform Desktop App**: Built on Rust Tauri for a small footprint and high performance.
- 🎨 **Modern UI**: Designed with Svelte 5 (Runes) and Tailwind CSS for a clean, beautiful interface.
- 📡 **Dual-Channel Communication**:
  - **Request Channel**: The frontend calls Rust via Tauri Commands, which then requests the Python backend (port 8888) to generate guides.
  - **Log Channel**: Rust runs a built-in HTTP server (port 9999) to receive real-time log streams from the Python backend and pushes them to the frontend via WebSocket.
- 📄 **PDF Export**: Clean log printing/PDF export functionality using CSS Print Media Query and DOM manipulation.
- 🔧 **Developer Friendly**: Fully configured for hot reloading and build processes.
## 🛠️ Tech Stack
- **Frontend**: SvelteKit, Svelte 5 (Runes), Tailwind CSS
- **Backend**: Rust (Tauri)
- **Network**: `tiny_http` (internal log server), `reqwest` (HTTP client)
- **Inter-Process**: Tauri Events
## 📋 Prerequisites
Before running this project, ensure your development environment has the following tools installed:
1. **Node.js** (v18 or higher recommended)
2. **pnpm** (Package manager)
3. **Rust** (and Cargo)
4. **Python Backend Service**: The application relies on a Python backend API running on `localhost:8888`.
## 🚀 Quick Start
### 1. Install Dependencies
```bash
pnpm install
```
### 2. Start Development Mode
This command will automatically start the frontend dev server (default port 1420) and compile the Tauri app.
```bash
pnpm tauri dev
```
> **Note**: Please ensure the Python backend service is already running on `localhost:8888`, otherwise the "Generate Travel Guides" function will report an error.
### 3. Build for Production
```bash
pnpm tauri build
```
The build artifacts will be located in the `src-tauri/target/release/bundle/` directory.
## 🏗️ Project Architecture
### Core Interaction Flow
This project uses Rust as an intermediary layer to decouple the Svelte frontend from the Python backend:
1. **Guide Generation Flow**:
   - The user fills in the City and Date Offset in the UI.
   - The frontend calls the Tauri Command `call_service`.
   - Rust (`lib.rs`) uses `reqwest` to send a POST request to `http://localhost:8888/generate`.
   - The result is returned to the frontend and displayed in the "Sender Result" area.
2. **Log Streaming Flow**:
   - When the Rust application starts, it automatically launches a `tiny_http` server on `127.0.0.1:9999`.
   - While processing tasks, the Python backend POSTs logs to `http://127.0.0.1:9999/log`.
   - Rust receives the logs and broadcasts them to the frontend using Tauri's `app.emit("log-line", ...)`.
   - The frontend listens to the `log-line` event and updates the "Travel Guides" list in real-time.
### Key File Breakdown
- **`src-tauri/src/lib.rs`**:
  - `call_service`: Handles frontend requests and forwards them to Python.
  - `start_log_server_impl`: Internal HTTP server that receives external logs and pushes them to the frontend.
- **`src/app.css`**:
  - Defines `@media print` styles. During printing, it automatically hides the Header and Main areas, displaying only the content in `#print-area`, and forces background color printing.
- **`src/routes/+page.svelte`** (Implied):
  - Uses Svelte 5 Runes (`$state`) for state management.
  - The `exportToPDF` function is responsible for sanitizing logs, injecting them into the DOM, and triggering the browser print dialog.
## 📜 License
MIT License
