Set-Location "C:\zwesta-trader\zwesta-v3-advanced\frontend"
$log = "C:\zwesta-trader\build_log.txt"
"BUILD START: $(Get-Date)" | Out-File $log
cmd /c "npm run build" 2>&1 | Out-File $log -Append
"BUILD END: $(Get-Date)" | Out-File $log -Append
Copy-Item -Path "dist\*" -Destination "C:\zwesta-trader-web\" -Recurse -Force
"DEPLOY DONE" | Out-File $log -Append
git add -- "zwesta-v3-advanced/frontend" 2>&1 | Out-File $log -Append
git commit -m "Deploy latest frontend build" 2>&1 | Out-File $log -Append
git push origin master 2>&1 | Out-File $log -Append
"ALL DONE: $(Get-Date)" | Out-File $log -Append
