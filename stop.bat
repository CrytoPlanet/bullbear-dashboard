@echo off
chcp 65001 >nul
echo ========================================
echo   停止 BullBear Dashboard 服务
echo ========================================
echo.

echo 正在查找并停止相关进程...

:: 停止后端服务（uvicorn）
taskkill /FI "WINDOWTITLE eq BullBear Backend*" /T /F >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"uvicorn" >nul
    if not errorlevel 1 (
        taskkill /PID %%a /F >nul 2>&1
        echo [已停止] 后端服务 (PID: %%a)
    )
)

:: 停止前端服务（vite）
taskkill /FI "WINDOWTITLE eq BullBear Frontend*" /T /F >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"vite" >nul
    if not errorlevel 1 (
        taskkill /PID %%a /F >nul 2>&1
        echo [已停止] 前端服务 (PID: %%a)
    )
)

echo.
echo 服务已停止！
echo.
pause

