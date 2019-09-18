Write-Host "Installing Erlang..." -ForegroundColor Cyan

Write-Host "Downloading..."
$exePath = "$($env:USERPROFILE)\otp_win64_22.1.exe"
(New-Object Net.WebClient).DownloadFile('http://www.erlang.org/download/otp_win64_22.1.exe', $exePath)

Write-Host "Installing..."
cmd /c start /wait $exePath /S
del $exePath

Remove-Path 'C:\Program Files\erl7.1\bin'
Remove-Path 'C:\Program Files\erl7.3\bin'
Remove-Path 'C:\Program Files\erl8.2\bin'
Remove-Path 'C:\Program Files\erl8.3\bin'
Remove-Path 'C:\Program Files\erl9.2\bin'

Add-Path 'C:\Program Files\erl10.4\bin'
[Environment]::SetEnvironmentVariable('ERLANG_HOME', 'C:\Program Files\erl10.4', 'Machine')

# C:\Program Files\erl10.4

$x64items = @(Get-ChildItem "HKLM:SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
$x64items + @(Get-ChildItem "HKLM:SOFTWARE\wow6432node\Microsoft\Windows\CurrentVersion\Uninstall") `
    | ForEach-object { Get-ItemProperty Microsoft.PowerShell.Core\Registry::$_ } `
    | Where-Object { $_.DisplayName -and $_.DisplayName.contains('Erlang') } `
    | Sort-Object -Property DisplayName `
    | Select-Object -Property DisplayName,DisplayVersion

Write-Host "Installed Erlang" -ForegroundColor Green