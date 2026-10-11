$printServiceDir = $PSScriptRoot
$pythonCommand = if ($env:KIOSK_PYTHON) { $env:KIOSK_PYTHON } else { 'python' }
& $pythonCommand (Join-Path $printServiceDir 'service.py') --initialize
if ($LASTEXITCODE -ne 0) { throw 'Print configuration could not be initialized' }
Start-Process -FilePath $pythonCommand -ArgumentList @('"' + (Join-Path $printServiceDir 'service.py') + '"') -WorkingDirectory $printServiceDir -WindowStyle Hidden
