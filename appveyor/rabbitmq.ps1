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


Write-Host "Installing RabbitMQ..." -ForegroundColor Cyan

Write-Host "Downloading..."
$exePath = "$($env:USERPROFILE)\rabbitmq-server-3.7.5.exe"
(New-Object Net.WebClient).DownloadFile('https://dl.bintray.com/rabbitmq/all/rabbitmq-server/3.7.5/rabbitmq-server-3.7.5.exe', $exePath)

Write-Host "Installing..."
cmd /c start /wait $exePath /S

$rabbitPath = 'C:\Program Files\RabbitMQ Server\rabbitmq_server-3.7.5'

Write-Host "Installing service..."
Start-Process -Wait "$rabbitPath\sbin\rabbitmq-service.bat" "install"

Write-Host "Starting service..."
Start-Process -Wait "$rabbitPath\sbin\rabbitmq-service.bat" "start"

Get-Service "RabbitMQ"

Write-Host "RabbitMQ installed and started" -ForegroundColor Green