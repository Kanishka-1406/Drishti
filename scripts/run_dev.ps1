$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$uvicorn = Join-Path $backend '.venv\Scripts\uvicorn.exe'
$alembic = Join-Path $backend '.venv\Scripts\alembic.exe'

if (-not (Test-Path -LiteralPath $python)) {
  throw 'Backend environment is missing. Run: cd backend; python -m venv .venv; .\.venv\Scripts\python.exe -m pip install -r requirements.txt'
}

Set-Location -LiteralPath $backend
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
  }
}
& $alembic upgrade head

$backendCommand = "Set-Location -LiteralPath '$backend'; Get-Content .env | ForEach-Object { if (`$_ -match '^\s*([^#][^=]*)=(.*)$') { [Environment]::SetEnvironmentVariable(`$matches[1].Trim(), `$matches[2].Trim(), 'Process') } }; & '$uvicorn' app.main:app --host 0.0.0.0 --port 8000"
$frontendCommand = "Set-Location -LiteralPath '$frontend'; npm run dev -- --host 127.0.0.1"
Start-Process powershell -ArgumentList '-NoExit','-Command',$backendCommand
Start-Process powershell -ArgumentList '-NoExit','-Command',$frontendCommand
Write-Host 'DRISHTI is starting. Open http://127.0.0.1:5173'
