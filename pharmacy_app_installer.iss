[Setup]
AppName=Pharmacy Management System
AppVersion=1.0
DefaultDirName={pf}\PharmacyManagementSystem
DefaultGroupName=Pharmacy Management System
OutputDir=dist
OutputBaseFilename=PharmacyManagementInstaller
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\pharmacy_app.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Pharmacy Management System"; Filename: "{app}\pharmacy_app.exe"
Name: "{group}\Uninstall Pharmacy Management System"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\pharmacy_app.exe"; Description: "Launch Pharmacy Management System"; Flags: nowait postinstall skipifsilent
