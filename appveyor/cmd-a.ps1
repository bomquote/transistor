# """
# transistor.appveyor.cmd-a
# ~~~~~~~~~~~~
# This is a powershell script to run a command.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """

Write-Host "Running cmd-a..." -ForegroundColor Cyan

Start-Job -ScriptBlock {D:\\host\\transistor\\appveyor\\cmd-a.cmd}

Write-Host "Started cmd-a..." -ForegroundColor Green