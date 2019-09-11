# """
# transistor.appveyor.postgresql
# ~~~~~~~~~~~~
# This is a powershell script to start postgresql on Windows.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """

Write-Host "Starting PostgreSQL server..." -ForegroundColor Cyan

Start-Job -ScriptBlock {D:\host\transistor\appveyor\postgresql.cmd}

Write-Host "Let's move on while PostgreSQL starts..." -ForegroundColor Green