param(
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\TechPulse'),
    [string]$PythonExecutable = 'python',
    [switch]$NoLaunch
)
$ErrorActionPreference = 'Stop'
$taskSourceRoot = Split-Path -Parent $PSScriptRoot
$taskInstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$taskSourcePath = [IO.Path]::GetFullPath($taskSourceRoot)
if ($taskInstallRoot -eq $taskSourcePath -or $taskSourcePath.StartsWith($taskInstallRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose a separate application installation directory.'
}
if ((Test-Path -LiteralPath $taskInstallRoot) -and -not (Test-Path -LiteralPath (Join-Path $taskInstallRoot 'techpulse-install.json'))) {
    if (@(Get-ChildItem -LiteralPath $taskInstallRoot -Force).Count -gt 0) {
        throw 'Existing folder is not a managed TechPulse installation. Choose an empty folder.'
    }
}
& $PythonExecutable -c 'import sys; assert (3,12) <= sys.version_info[:2] < (3,15)'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12-3.14 is required.' }
New-Item -ItemType Directory -Force -Path $taskInstallRoot | Out-Null
$taskRuntime = Join-Path $taskInstallRoot 'runtime'
$taskPython = Join-Path $taskRuntime 'Scripts\python.exe'
$taskPythonw = Join-Path $taskRuntime 'Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    & $PythonExecutable -m venv $taskRuntime
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the dedicated application runtime.' }
}
& $taskPython -m pip install --disable-pip-version-check --require-hashes -r (Join-Path $taskSourceRoot 'requirements.lock')
if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed; existing research data was not changed.' }

# Copy only application code/assets and documentation; never databases, Git or scratch files.
$taskModuleSource = Join-Path $taskSourceRoot 'src\techpulse'
$taskModuleTarget = Join-Path $taskInstallRoot 'app\src\techpulse'
New-Item -ItemType Directory -Force -Path $taskModuleTarget | Out-Null
Get-ChildItem -LiteralPath $taskModuleSource -File -Filter '*.py' | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $taskModuleTarget $_.Name) -Force
}
New-Item -ItemType Directory -Force -Path (Join-Path $taskModuleTarget 'assets') | Out-Null
Copy-Item -LiteralPath (Join-Path $taskModuleSource 'assets\techpulse.svg') -Destination (Join-Path $taskModuleTarget 'assets\techpulse.svg') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'desktop_launcher.pyw') -Destination (Join-Path $taskInstallRoot 'TechPulse.pyw') -Force
foreach ($taskDocument in @('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'requirements.lock')) {
    Copy-Item -LiteralPath (Join-Path $taskSourceRoot $taskDocument) -Destination (Join-Path $taskInstallRoot $taskDocument) -Force
}
$taskDocs = Join-Path $taskInstallRoot 'docs'
New-Item -ItemType Directory -Force -Path $taskDocs | Out-Null
foreach ($taskDocument in @('USER_GUIDE.md', 'IMPORT_FORMATS.md', 'REQUIREMENTS.md')) {
    Copy-Item -LiteralPath (Join-Path $taskSourceRoot ('docs\' + $taskDocument)) -Destination (Join-Path $taskDocs $taskDocument) -Force
}
$taskIcon = Join-Path $taskInstallRoot 'TechPulse.ico'
& $taskPython (Join-Path $PSScriptRoot 'make_icon.py') (Join-Path $taskModuleTarget 'assets\techpulse.svg') $taskIcon
if ($LASTEXITCODE -ne 0) { throw 'Could not render the application icon.' }

$taskShell = New-Object -ComObject WScript.Shell
$taskDesktop = Join-Path ([Environment]::GetFolderPath('Desktop')) 'TechPulse.lnk'
$taskMenu = Join-Path ([Environment]::GetFolderPath('Programs')) 'TechPulse'
New-Item -ItemType Directory -Force -Path $taskMenu | Out-Null
$taskLinks = @($taskDesktop, (Join-Path $taskMenu 'TechPulse.lnk'))
foreach ($taskLink in $taskLinks) {
    if (Test-Path -LiteralPath $taskLink) {
        $taskExisting = $taskShell.CreateShortcut($taskLink)
        if ($taskExisting.TargetPath -ne $taskPythonw) { throw 'An unrelated TechPulse shortcut already exists; it was not overwritten.' }
    }
    $taskShortcut = $taskShell.CreateShortcut($taskLink)
    $taskShortcut.TargetPath = $taskPythonw
    $taskShortcut.Arguments = '"' + (Join-Path $taskInstallRoot 'TechPulse.pyw') + '"'
    $taskShortcut.WorkingDirectory = $taskInstallRoot
    $taskShortcut.IconLocation = $taskIcon + ',0'
    $taskShortcut.Description = 'TechPulse financial research terminal - local research preview'
    $taskShortcut.Save()
}
$taskHashes = @{}
Get-ChildItem -LiteralPath $taskModuleTarget -File -Filter '*.py' | ForEach-Object {
    $taskHashes[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
}
@{ app = 'TechPulse'; version = '0.1.0 development preview'; installed_at = [DateTime]::UtcNow.ToString('o'); install_root = $taskInstallRoot; runtime = $taskPythonw; shortcuts = $taskLinks; source_hashes = $taskHashes } |
    ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $taskInstallRoot 'techpulse-install.json') -Encoding utf8
Write-Output ('Installed TechPulse: ' + $taskInstallRoot)
Write-Output ('Desktop shortcut: ' + $taskDesktop)
if (-not $NoLaunch) {
    Start-Process -FilePath $taskPythonw -ArgumentList ('"' + (Join-Path $taskInstallRoot 'TechPulse.pyw') + '"') -WorkingDirectory $taskInstallRoot -WindowStyle Normal | Out-Null
}
