# TravelGuide Multi-Agent System
An intelligent travel advice system built on the OpenAgents framework that generates personalized travel recommendations based on real-time weather data.
## 📋 Project Overview
This project demonstrates a multi-agent collaborative workflow:
1. The **Weather Connector** receives user requests and fetches real-time weather data.
2. Tasks are delegated to four student Agents representing different Hogwarts houses (Gryffindor, Slytherin, Ravenclaw, Hufflepuff).
3. Each Agent generates travel advice based on their unique personality traits.
4. Results are aggregated and displayed.
### System Features
- 🦁 **Gryffindor**: Focuses on bravery, adventure, and outdoor challenges.
- 🐍 **Slytherin**: Focuses on strategic planning, efficiency, and resource management.
- 🦅 **Ravenclaw**: Focuses on learning, growth, knowledge, and exploration.
- 🦡 **Hufflepuff**: Focuses on comfort, food, relaxation, and a friendly atmosphere.
## 🏗️ System Architecture
```
User Request
    ↓
Weather Connector (HTTP Server :8888)
    ↓
Fetch Weather Data → Open-Meteo API
    ↓
Delegate Tasks (Sequential) → Four House Agents
    ↓
Collect Advice → Send to Log Server (:9999)
    ↓
Display Results in Terminal
```
## 📦 Prerequisites
- Python 3.8+
- OpenAgents (installed via pip)
- Local Area Network (LAN) environment
## 🚀 Quick Start
### 1. Install Dependencies
```bash
pip install openagents aiohttp psutil requests
```
### 2. Configure LLM
Edit `llm_config.json` to configure your LLM service:
```json
{
  "DEFAULT_LLM_PROVIDER": "custom",
  "DEFAULT_LLM_BASE_URL": "http://localhost:11434/v1",
  "DEFAULT_LLM_API_KEY": "not-required",
  "DEFAULT_LLM_MODEL_NAME": "gpt-oss:20b"
}
```
### 3. Launch the System
**Method 1: One-Click Start (Recommended)**
```bash
python launch.py all
```
This will start the following in order:
- The OpenAgents Network node
- The four House Agents
- The Weather Connector
**Method 2: Manual Start**
```bash
# Terminal 1: Start Network
openagents network start .
# Terminal 2: Start Log Server
python log_server.py
# Terminal 3: Start Weather Connector
python agents/weather_connector.py
# Terminal 4: Start House Agents (as needed)
openagents agent start agents/gryffindor-student.yaml
openagents agent start agents/hufflepuff-student.yaml
# ...
```
### 4. Send Requests
**Using the client script:**
```bash
python weather_client.py Beijing
python weather_client.py Shanghai 1  # 1 means tomorrow
```
**Using curl:**
```bash
curl -X POST http://localhost:8888/generate \
  -H "Content-Type: application/json" \
  -d '{"city": "Beijing"}'
```
## 📂 Project Structure
```
.
├── agents/
│   ├── gryffindor-student.yaml    # Gryffindor Agent Config
│   ├── hufflepuff-student.yaml    # Hufflepuff Agent Config
│   ├── slytherin-student.yaml     # Slytherin Agent Config
│   ├── ravenclaw-student.yaml     # Ravenclaw Agent Config
│   ├── weather_connector.py       # Weather Coordinator
├── tools/
│   ├── weather.py                 # Weather Service Module
│   └── send_result.py             # Result Sending Utility
├── tests/
│   └── weather_client.py          # HTTP Test Client
│   └── log_server.py              # Log Server
├── logs/                          # Runtime Logs Directory (Auto-created)
├── llm_config.json                # LLM Configuration
├── network.yaml                   # Network Configuration
├── launch.py                      # One-Click Launch Script
└── README.md                      # This file
```
## ⚙️ Configuration Details
### Network Configuration (`network.yaml`)
- **Ports**: HTTP 8700, gRPC 8600
- **Authentication**: Password authentication enabled by default (workers and coordinators use the same hash)
- **Timeouts**: Agent timeout set to 180s, message timeout set to 120s
### Agent Configuration
Each Agent's YAML configuration includes:
- **Agent ID & Type**: Unique identifier.
- **Instruction**: Defines the Agent's personality and strict output format.
- **Triggers**: Responds to task assignment events.
- **Connection**: Host, port, and password hash.
## 🌤️ Workflow Details
1. **Receive Request**: Weather Connector listens on `0.0.0.0:8888/generate`.
2. **Fetch Weather**: Calls the Open-Meteo API to get weather for the specified city and date.
3. **Sequential Delegation**: Delegates tasks in a fixed order (Gryffindor → Slytherin → Ravenclaw → Hufflepuff).
4. **Wait for Results**: Each Agent returns results via the `task.notification.completed` event.
5. **Send Logs**: Uses `send_result_to_server()` to send results to the log server.
6. **Display Output**: The log server formats and prints the results.
## 🔧 Troubleshooting
### Cannot connect to weather_connector
- Ensure `weather_connector` is running.
- Check if port 8888 is occupied.
- Review the log file at `logs/weather_connector_*.log`.
### Agent Task Timeout
- Check if your LLM service is running correctly.
- Increase the `agent_timeout` value in `network.yaml`.
- Check `TASK_TIMEOUT_SECONDS` in `weather_connector.py`.
### Character Encoding Issues
The launch script automatically sets UTF-8 encoding. If issues persist, check your terminal's encoding settings.
### Process Cleanup
If residual processes remain, `launch.py` attempts to clean them up on exit. To clean manually:
```bash
# Windows
taskkill /F /IM python.exe
# Linux/Mac
pkill -f weather_connector
pkill -f openagents
```
## 📊 Logging
All log files are saved in the `logs/` directory with the naming format `{type}_{name}_{timestamp}.log`:
- `network_*.log` - OpenAgents network node logs.
- `agent_*_*.log` - Runtime logs for each Agent.
- `script_*_*.log` - Custom script logs (weather_connector).
## 🎯 Use Cases
This system is designed specifically for **LAN environments** and is suitable for:
- Personal learning of multi-agent collaborative development.
- OpenAgents framework demonstrations.
## 📝 Output Example
```
============================================================================
📩 [14:30:25] Received message from Agent: gryffindor-student
------------------------------------------------------------
🦁 **Gryffindor Recommendation**
Beijing, 2026-01-31
A true Gryffindor never retreats in the face of cold winds!
⚔️ **Warrior's Guide**
- Wear a warm coat and gloves.
- Climb the Great Wall and challenge yourself.
- Experience outdoor hiking.
💪 **Motto**
Courage is not the absence of fear, but moving forward despite it!
============================================================================
```
## 🔐 Security Notes
- Uses the `coordinators` group password hash for authentication by default.
- **For production**, please modify the `password_hash` in `network.yaml`.
- The log server binds to `0.0.0.0`, making it accessible within the LAN.
## 📄 License
MIT License - See header in source files for details.
## 👥 Contributing
Issues and Pull Requests are welcome!
## Acknowledgments

This project is built upon the following excellent open-source tools and services:

    OpenAgents : A powerful framework for orchestrating multi-agent workflows.
    Open-Meteo : For providing the free, open-source weather API that powers this system.
    aiohttp : For the asynchronous HTTP client/server implementation.
    psutil : For cross-platform process management.

License & Commercial Usage Notice
Open-Meteo API Usage Policy

⚠️ Important: This project integrates the free API provided by Open-Meteo.

    Non-Commercial Use Only: The free tier of the Open-Meteo API is strictly licensed for non-commercial purposes.
    Commercial Restriction: If you intend to deploy this system for commercial use (e.g., selling the service, using it in a business environment, or integrating it into a commercial product), you must obtain a commercial license from Open-Meteo or switch to a licensed weather data provider.
    Attribution: Please refer to Open-Meteo’s Terms of Use for the most up-to-date licensing requirements.

OpenAgents Framework

This project utilizes the OpenAgents framework. Please ensure you comply with the license of the OpenAgents framework (typically Apache 2.0 or MIT, refer to the official repository for details).
Project License

## 📧 Contact
For questions, please refer to the project documentation or submit an issue.
