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

Write-Host "Running cmd-b..." -ForegroundColor Cyan

Start-Job -ScriptBlock {D:\\host\\transistor\\appveyor\\cmd-b.cmd}

Write-Host "Started cmd-b..." -ForegroundColor Green