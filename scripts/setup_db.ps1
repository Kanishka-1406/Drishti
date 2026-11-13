$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw 'Docker is not installed. Install Docker Desktop and start it first.'
}
docker compose up -d db
docker compose run --rm backend alembic upgrade head
Write-Host 'PostgreSQL/PostGIS schema is ready.'
