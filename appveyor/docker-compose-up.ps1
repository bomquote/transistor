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

Set-Location -Path X:\host\transistor\appveyor\aquarium

Start-Job -ScriptBlock {C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe up}

Write-Host "Let's move on while Aquarium starts..." -ForegroundColor Green