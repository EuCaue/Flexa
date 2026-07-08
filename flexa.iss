[Setup]
; Identificadores do App
AppName=Flexa
AppVersion=1.0.0
AppPublisher=Cauê
AppPublisherURL=https://github.com/eucaue/flexa
AppSupportURL=https://github.com/eucaue/flexa/issues
AppUpdatesURL=https://github.com/eucaue/flexa/releases

; Configurações de Saída
DefaultDirName={autopf}\Flexa
DefaultGroupName=Flexa
DisableProgramGroupPage=yes
OutputBaseFilename=Flexa-Windows-Installer
OutputDir=dist
Compression=lzma2/ultra64
SolidCompression=yes

; Configurações de Ícone (se tiver um .ico, descomente a linha abaixo)
SetupIconFile=data\icons\flexa.ico
UninstallDisplayIcon={app}\flexa.exe

; Privilégios (lowest = instala apenas para o usuário atual, admin = para todos os usuários)
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia o executável principal e tudo que está na pasta gerada pelo PyInstaller
Source: "dist\flexa\flexa.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\flexa\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Cria atalhos no Menu Iniciar e na Área de Trabalho
Name: "{group}\Flexa"; Filename: "{app}\flexa.exe"
Name: "{autodesktop}\Flexa"; Filename: "{app}\flexa.exe"; Tasks: desktopicon

[Run]
; Opção para rodar o app logo após instalar
Filename: "{app}\flexa.exe"; Description: "{cm:LaunchProgram,Flexa}"; Flags: nowait postinstall skipifsilent
