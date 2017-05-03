; -- Example2.iss --
; Same as Example1.iss, but creates its icon in the Programs folder of the
; Start Menu instead of in a subfolder, and also creates a desktop icon.

; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppName=Ema
AppVersion=1.1
DefaultDirName={pf}\Ema
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\Ema.exe

[Files]
Source: ".win32\dist\ema\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{commonprograms}\Ema"; Filename: "{app}\Ema.exe"
Name: "{commondesktop}\Ema"; Filename: "{app}\Ema.exe"
