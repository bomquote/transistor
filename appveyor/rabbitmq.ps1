# """
# transistor.appveyor.rabbitmq
# ~~~~~~~~~~~~
# This is a powershell script to install rabbitmq on Windows.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """
# check the discussion at https://github.com/appveyor/ci/issues/307
# installs into C:\Program Files\RabbitMQ Server


$rabbitVersion = '3.7.27'

Write-Host "Installing RabbitMQ $rabbitVersion..." -ForegroundColor Cyan

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "Downloading..."
$exePath = "$env:TEMP\rabbitmq-server-$rabbitVersion.exe"
(New-Object Net.WebClient).DownloadFile("https://github.com/rabbitmq/rabbitmq-server/releases/download/v$rabbitVersion/rabbitmq-server-$rabbitVersion.exe", $exePath)

Write-Host "Installing..."
cmd /c start /wait $exePath /S

$rabbitPath = "${env:ProgramFiles}\RabbitMQ Server\rabbitmq_server-$rabbitVersion"

Write-Host "Installing service..."
Start-Process -Wait "$rabbitPath\sbin\rabbitmq-service.bat" "install"

Write-Host "Starting service..."
Start-Process -Wait "$rabbitPath\sbin\rabbitmq-service.bat" "start"

Get-Service "RabbitMQ"

Write-Host "RabbitMQ installed and started" -ForegroundColor Green

Write-Host "Installing RabbitMQ plugins..." -ForegroundColor Cyan

Write-Host "Downloading..."
$zipPath = "$env:TEMP\rabbitmq_delayed_message_exchange-20171201-3.7.x.zip"
$pluginPath = "${env:ProgramFiles}\RabbitMQ Server\rabbitmq_server-$rabbitVersion\plugins"
(New-Object Net.WebClient).DownloadFile('https://bintray.com/rabbitmq/community-plugins/download_file?file_path=3.7.x%2Frabbitmq_delayed_message_exchange%2Frabbitmq_delayed_message_exchange-20171201-3.7.x.zip', $zipPath)
7z x $zipPath -y -o"$pluginPath" | Out-Null

Write-Host "Installing..."
& "${env:ProgramFiles}\RabbitMQ Server\rabbitmq_server-$rabbitVersion\sbin\rabbitmq-plugins.bat" enable rabbitmq_delayed_message_exchange
& "${env:ProgramFiles}\RabbitMQ Server\rabbitmq_server-$rabbitVersion\sbin\rabbitmq-plugins.bat" enable rabbitmq_management

# Management URL: http://127.0.0.1:15672/
# Username/password: guest/guest

Write-Host "RabbitMQ plugins installed and started" -ForegroundColor Green