# """
# transistor.appveyor.docker-compose-up
# ~~~~~~~~~~~~
# This is a powershell script to `run docker-compose up` command on Aquarium.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """

Write-Host "Installing Aquarium..." -ForegroundColor Cyan

$cmdPath = "x:\host\transistor\aquarium\docker.cmd"

Write-Host "Starting aquarium service with docker-compose up..."
cmd /c start /wait $cmdPath /S

Write-Host "Aquarium installed and started" -ForegroundColor Green