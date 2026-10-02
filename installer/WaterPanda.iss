#define MyAppName "Water Panda"
#define MyAppVersion "25.0.2"
#define MyAppPublisher "Kritika Gupta"
#define MyAppExeName "WaterPanda.exe"

[Setup]
AppId={{C092CA8D-8E07-4D27-A4C8-74837663FB54}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\WaterPuppy
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=Water_Panda_Setup
SetupIconFile=..\assets\panda.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\dist\WaterPanda\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Water Panda"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\panda.ico"
Name: "{autodesktop}\Water Panda"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\panda.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Start Water Panda"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /IM WaterPanda.exe /F"; Flags: runhidden; RunOnceId: "StopWaterPanda"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\WaterPanda.exe"
Type: files; Name: "{app}\README.md"
Type: filesandordirs; Name: "{app}\assets"

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
    MsgBox('Your water history, reminders and settings remain in the WaterPuppy folder so a future reinstall can restore them.', mbInformation, MB_OK);
end;
