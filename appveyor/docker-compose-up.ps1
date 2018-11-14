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

Install-Module snek

Use-Python {
    $dg = Import-PythonModule "subprocess"
    $dg.call("x:\host\transistor\appveyor\docker-compose-up.cmd")
} -Version v3

Write-Host "Let's move on while Aquarium starts..." -ForegroundColor Green