[Setup]
AppName=wAgent
AppVersion=1.0.0
DefaultDirName={autopf}\wAgent
DefaultGroupName=wAgent
OutputBaseFilename=wAgent_setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "E:\LLM\Agent\wAgent\dist\wAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\LLM\Agent\wAgent\config.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\LLM\Agent\wAgent\core\*"; DestDir: "{app}\core"; Flags: ignoreversion recursesubdirs
Source: "E:\LLM\Agent\wAgent\ui\*"; DestDir: "{app}\ui"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\wAgent"; Filename: "{app}\wAgent.exe"
