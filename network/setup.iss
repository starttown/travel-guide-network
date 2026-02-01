; Travel Guide Network - 安装脚本
; 文件位置：network/setup.iss

[Setup]
AppName=Travel Guide Network
AppVersion=1.0.0
AppVerName=Travel Guide Network 1.0.0
AppPublisher=starttown
AppPublisherURL=https://github.com/starttown/travel-guide-network.git

; 默认安装目录
DefaultDirName={pf}\TravelGuideNetwork
; 默认开始菜单组
DefaultGroupName=Travel Guide Network

; 输出配置
OutputBaseFilename=TravelGuideNetwork-Setup
OutputDir=.\Output
Compression=lzma2
SolidCompression=yes

; 权限配置
PrivilegesRequired=admin

; 卸载图标
UninstallDisplayIcon={app}\run_network.bat

; 安装程序界面设置
WizardStyle=modern
DisableDirPage=no
DisableProgramGroupPage=no

[Files]
; 打包当前目录 (network) 下的所有业务文件
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.log,Output,setup.iss"

; 打包 python_runtime 目录（python_runtime 就在当前 network 目录下）
Source: "python_runtime\*"; DestDir: "{app}\python_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 开始菜单快捷方式
Name: "{group}\Travel Guide Network"; Filename: "{app}\run_network.bat"

; 桌面快捷方式
Name: "{commondesktop}\Travel Guide Network"; Filename: "{app}\run_network.bat"

[Run]
; 安装完成后可以选择是否运行程序
Name: "{app}\run_network.bat"; Description: "启动 Travel Guide Network"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 卸载时清理
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
