#define MyAppName "Encoding Converter"
#define MyAppNameCN "编码转换器"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "EncodingConverter"
#define MyAppURL "https://github.com/cooleye/encoding-converter"
#define MyAppExeName "EncodingConverter.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\EncodingConverter
DisableProgramGroupPage=yes
OutputDir=D:\trae_space\encoding-converter\dist
OutputBaseFilename=EncodingConverter-Setup-v{#MyAppVersion}
SetupIconFile=D:\trae_space\encoding-converter\packaging\assets\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\trae_space\encoding-converter\dist\EncodingConverter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\trae_space\encoding-converter\logo.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\trae_space\encoding-converter\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "{#MyAppNameCN}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "{#MyAppNameCN}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
