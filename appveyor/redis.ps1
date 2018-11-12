# """
# transistor.appveyor.redis
# ~~~~~~~~~~~~
# This is a powershell script to install redis in a windows server environment.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """
Add-Type -assembly "system.io.compression.filesystem"
$source="https://github.com/MicrosoftArchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.zip"
$destination="c:\redisarchive"
Invoke-WebRequest $source -OutFile $destination
[IO.Compression.ZipFile]::ExtractToDirectory('c:\redisarchive', 'c:\redis-3.2.100')

cd c:\redis-3.2.100
.\redis-server.exe --service-install
.\redis-server.exe --service-start
cd ..