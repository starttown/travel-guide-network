; Travel Guide Network - 安装脚本 (位于 network 目录下)
; 使用 Inno Setup Compiler 编译

[Setup]
AppName=Travel Guide Network
AppVersion=1.0.0
DefaultDirName={pf}\TravelGuideNetwork
DefaultGroupName=Travel Guide Network
OutputBaseFilename=TravelGuideNetwork-Setup
Compression=lzma2
SolidCompression=yes
; 👇 关键修改：请求管理员权限安装
PrivilegesRequired=admin
; 输出目录指定在 network 下的 Output 文件夹，方便查找
OutputDir=.\Output
UninstallDisplayIcon={app}\run_network.bat

[Files]
; 打包当前目录 (network) 下的所有文件
Source: "*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "*.log,Output,installer.iss,run_network.bat"

Source: "python_runtime\*"; DestDir: "{app}\python_runtime"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 👇 关键修改：添加 Verb: runas 让双击快捷方式时也以管理员身份运行
Name: "{group}\Travel Guide Network"; Filename: "{app}\run_network.bat"; 
Name: "{commondesktop}\Travel Guide Network"; Filename: "{app}\run_network.bat"; 

[Run]
; 安装完成后不自动启动

[UninstallDelete]
; 卸载时清理
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\__pycache__"
