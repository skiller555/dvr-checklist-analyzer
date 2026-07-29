; DVR Checklist Analyzer - Inno Setup Script
#define MyAppName "DVR Checklist Analyzer"
#define MyAppVersion "1.0"
#define MyAppPublisher "CONTEA - PARTNERS"
#define MyAppExeName "DVR_Checklist_Analyzer.exe"
#define SourceDir "C:\Users\d.delisa.CONTEA\.gemini\antigravity\scratch\dvr_checklist_analyzer\dist\DVR_Checklist_Analyzer"

[Setup]
AppId={{A3F7B8C2-4D91-4E6A-8B3F-2C5E7D9A1B4F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\CONTEA Partners\DVR Checklist Analyzer
DefaultGroupName=CONTEA Partners\DVR Checklist Analyzer
AllowNoIcons=yes
OutputDir=C:\Users\d.delisa.CONTEA\Desktop
OutputBaseFilename=DVR_Checklist_Analyzer_SETUP_v1.0
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=no
DisableProgramGroupPage=auto

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia DVR Checklist Analyzer"; Flags: nowait postinstall skipifsilent
