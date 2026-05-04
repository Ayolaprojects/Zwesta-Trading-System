Set-Location "C:\zwesta-trader\zwesta-v3-advanced\frontend"
Write-Host "=== BUILDING ==="
cmd /c "npm run build" 2>&1 | Select-Object -Last 20
Write-Host "=== DEPLOYING ==="
Copy-Item -Path "dist\*" -Destination "C:\zwesta-trader-web\" -Recurse -Force
Write-Host "=== PUSHING TO GIT ==="
git add -- "zwesta-v3-advanced/frontend"
git commit -m "Deploy latest frontend build" 2>&1
git push origin master 2>&1
Write-Host "=== ALL DONE ==="
