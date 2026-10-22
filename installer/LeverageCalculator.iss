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
Source: "..\dist\LeverageCalculator\LeverageCalculator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\LeverageCalculator\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Leverage Calculator"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\Leverage Calculator"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch Leverage Calculator"; Flags: nowait postinstall skipifsilent

[Code]
// The updater passes the PID of the old desktop process. Waiting for it to
// terminate avoids an Inno Setup Restart Manager race while replacing its EXE.
// Normal manual installs do not pass UPGRADEPID and are unaffected.
function OpenProcess(DesiredAccess: DWORD; InheritHandle: BOOL; ProcessId: DWORD): THandle;
  external 'OpenProcess@kernel32.dll stdcall';
function WaitForSingleObject(Handle: THandle; Milliseconds: DWORD): DWORD;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function CloseHandle(Handle: THandle): BOOL;
  external 'CloseHandle@kernel32.dll stdcall';
function WindowsLastError(): DWORD;
  external 'GetLastError@kernel32.dll stdcall';

function InitializeSetup(): Boolean;
var
  PidText: String;
  ParentPid: Integer;
  ParentHandle: THandle;
  WaitResult: DWORD;
  ErrorCode: DWORD;
begin
  Result := True;
  PidText := ExpandConstant('{param:UPGRADEPID|}');
  if PidText = '' then
    Exit;

  ParentPid := StrToIntDef(PidText, 0);
  if ParentPid <= 0 then
  begin
    MsgBox('Invalid update process identifier. Start setup manually.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // SYNCHRONIZE = $00100000; WAIT_OBJECT_0 = 0.
  ParentHandle := OpenProcess($00100000, False, ParentPid);
  if ParentHandle = 0 then
  begin
    ErrorCode := WindowsLastError();
    // 87 = ERROR_INVALID_PARAMETER: original process has already exited.
    if ErrorCode <> 87 then
    begin
      MsgBox('Unable to verify that the old application has closed. Close Leverage Calculator, then run setup again.', mbError, MB_OK);
      Result := False;
    end;
    Exit;
  end;

  try
    // Bound the wait to 60 seconds. Never kill the user process or bypass a lock.
    WaitResult := WaitForSingleObject(ParentHandle, 60000);
    if WaitResult <> 0 then
    begin
      MsgBox('Leverage Calculator has not exited yet. Close it fully and run setup again.', mbError, MB_OK);
      Result := False;
    end;
  finally
    CloseHandle(ParentHandle);
  end;
end;
