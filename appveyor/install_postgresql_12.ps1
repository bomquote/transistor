Write-Host "Temporary solution to install PostgreSql 12.1 (as recommended by Feodor Fitsner): https://help.appveyor.com/discussions/problems/25522-postgresql-12"
Write-Host "Downloading PostgreSql 12.1..." -ForegroundColor Yellow
$exePath = "$env:TEMP\postgresql-12.1-1-windows-x64.exe"
(New-Object Net.WebClient).DownloadFile('https://get.enterprisedb.com/postgresql/postgresql-12.1-1-windows-x64.exe', $exePath)
Write-Host "Installing PostgreSql 12.1..." -ForegroundColor Yellow
cmd /c start /wait $exePath --mode unattended --install_runtimes 0 --superpassword Password12!
Write-Host "PostgreSql 12.1 installed" -ForegroundColor Green
$env:path = "C:\Program Files\PostgreSQL\12\bin;$env:path"