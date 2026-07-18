param(
    [int]$Port = 9000,
    [string]$RuleName = 'Zwesta Backend API'
)

$ErrorActionPreference = 'Stop'

$existing = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Firewall rule already exists: $RuleName" -ForegroundColor Yellow
    exit 0
}

New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
Write-Host "Firewall rule created for TCP port $Port" -ForegroundColor Green
