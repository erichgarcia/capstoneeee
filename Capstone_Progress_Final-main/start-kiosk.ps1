param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$frontend = Join-Path $PSScriptRoot 'queuing-system-frontend'
$logs = Join-Path $PSScriptRoot '.kiosk-launcher'
New-Item -ItemType Directory -Force -Path $logs | Out-Null
$mutex = New-Object System.Threading.Mutex($false, 'Local\CapstoneQueueKioskLauncher')
$locked = $false

function Test-Url([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch { return $false }
}

function Wait-Url([string]$Url, [string]$Label) {
    $deadline = (Get-Date).AddSeconds(60)
    do {
        if (Test-Url $Url) { return }
        Start-Sleep -Milliseconds 750
    } while ((Get-Date) -lt $deadline)
    throw "$Label did not become ready. Check the logs in $logs."
}

function Test-DatabasePort([string]$HostName, [int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $attempt = $client.ConnectAsync($HostName, $Port)
        return $attempt.Wait(1500) -and $client.Connected
    } catch { return $false } finally { $client.Dispose() }
}

try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { exit 0 }

    $node = (Get-Command node -ErrorAction Stop).Source
    $php = (Get-Command php -ErrorAction Stop).Source
    if (-not (Test-Path (Join-Path $frontend 'node_modules/vite/bin/vite.js'))) {
        throw 'Frontend dependencies are missing. Complete the one-time npm install in queuing-system-frontend first.'
    }
    $backend = Join-Path $PSScriptRoot 'queuing-system-backend'
    if (-not (Test-Path (Join-Path $backend 'vendor/autoload.php'))) {
        throw 'Backend dependencies are missing. Complete the one-time composer install first.'
    }
    $envFile = Join-Path $backend '.env'
    if (-not (Test-Path $envFile)) { throw 'The backend .env configuration is missing.' }
    $settings = @{}
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*(DB_HOST|DB_PORT|DB_CONNECTION)\s*=\s*(.*?)\s*$') {
            $settings[$matches[1]] = $matches[2].Trim('"', "'")
        }
    }
    $dbHost = if ($settings.DB_HOST) { $settings.DB_HOST } else { '127.0.0.1' }
    $dbPort = if ($settings.DB_PORT) { [int]$settings.DB_PORT } else { 3306 }
    if ($settings.DB_CONNECTION -ne 'sqlite' -and -not (Test-DatabasePort $dbHost $dbPort)) {
        if ($dbHost -notin @('localhost', '127.0.0.1')) {
            throw "The database at ${dbHost}:$dbPort is unavailable."
        }
        $xampp = Split-Path (Split-Path $php -Parent) -Parent
        $mysql = Join-Path $xampp 'mysql/bin/mysqld.exe'
        $mysqlConfig = Join-Path $xampp 'mysql/bin/my.ini'
        if (-not (Test-Path $mysql) -or -not (Test-Path $mysqlConfig)) {
            throw 'Cannot find XAMPP MySQL beside PHP. Start your database service and try again.'
        }
        Start-Process -FilePath $mysql -ArgumentList @("--defaults-file=`"$mysqlConfig`"", '--standalone') -WorkingDirectory $xampp -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'mysql-out.log') -RedirectStandardError (Join-Path $logs 'mysql-error.log') | Out-Null
        $deadline = (Get-Date).AddSeconds(30)
        while (-not (Test-DatabasePort $dbHost $dbPort)) {
            if ((Get-Date) -gt $deadline) { throw 'MySQL could not start. Check mysql-error.log in .kiosk-launcher.' }
            Start-Sleep -Milliseconds 750
        }
    }

    $kioskUrl = 'http://localhost:3000/'
    $apiUrl = 'http://127.0.0.1:8000/api/health/database'
    $frontendReady = Test-Url $kioskUrl
    $backendReady = Test-Url $apiUrl
    if (-not $frontendReady -and -not $backendReady) {
        $launcher = Join-Path $frontend 'scripts/dev.mjs'
        Start-Process -FilePath $node -ArgumentList @("`"$launcher`"") -WorkingDirectory $frontend -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logs 'system-out.log') -RedirectStandardError (Join-Path $logs 'system-error.log') | Out-Null
    } elseif (-not $frontendReady -or -not $backendReady) {
        throw 'Only part of the system is running. Close any existing development servers, then try again. See .kiosk-launcher logs if the database health check fails.'
    }
    Wait-Url $apiUrl 'Laravel and the database'
    Wait-Url 'http://localhost:3000/api/health/database' 'The kiosk API connection'
    Wait-Url $kioskUrl 'The kiosk'
    if (-not $NoBrowser) { Start-Process $kioskUrl }
} catch {
    $message = $_.Exception.Message
    Add-Content -Path (Join-Path $logs 'launcher-error.log') -Value "$(Get-Date -Format o) $message"
    if ($NoBrowser) { Write-Error $message } else {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($message, 'Kiosk could not start', 'OK', 'Error') | Out-Null
    }
    exit 1
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
