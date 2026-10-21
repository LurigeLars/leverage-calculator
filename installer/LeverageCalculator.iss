#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

#define AppName "Leverage Calculator"
#define AppExe "LeverageCalculator.exe"

[Setup]
AppId={{AC4360F2-9DA2-4E6D-96E1-942FC3B07745}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Leverage Calculator contributors
AppPublisherURL=https://github.com/LurigeLars/leverage-calculator
AppSupportURL=https://github.com/LurigeLars/leverage-calculator/issues
AppUpdatesURL=https://github.com/LurigeLars/leverage-calculator/releases
DefaultDirName={localappdata}\Programs\LeverageCalculator
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=LeverageCalculator-Setup
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
DisableProgramGroupPage=yes

[Files]
Source: "..\dist\LeverageCalculator.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Leverage Calculator"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\Leverage Calculator"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch Leverage Calculator"; Flags: nowait postinstall skipifsilent
