@echo off
chcp 65001 >nul
echo ========================================
echo   BullBear Dashboard 一键启动脚本
echo ========================================
echo.


echo [1/2] 启动后端服务...
cd backend
start "BullBear Backend" cmd /k "python -m uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
cd ..

echo [2/2] 启动 Vue 前端...
cd frontend
start "BullBear Frontend" cmd /k "pnpm dev"
cd ..

echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo 后端API: http://localhost:8000
echo Vue前端: http://localhost:5173
echo API文档: http://localhost:8000/docs
echo.
echo 提示: 
echo - 两个服务窗口已打开，关闭窗口即可停止对应服务
echo - 浏览器将自动打开前端应用
echo - 如果没有自动打开，请手动访问上述地址
echo.
timeout /t 5 >nul

:: 尝试打开浏览器（等待服务启动）
timeout /t 3 >nul
start http://localhost:5173 >nul 2>&1

echo 按任意键退出此窗口（服务将继续运行）...
pause >nul

