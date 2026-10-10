@echo off
chcp 65001 >nul
title 车小智 · 数据桥接启动器
cd /d "%~dp0"

set PY=C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
if not exist "%PY%" set PY=python

echo ============================================================
echo   车小智 · 新能源汽车智能检测系统 — 数据桥接
echo ============================================================
echo.

rem ---- 先清掉可能残留的旧进程 ----
for /f "tokens=2 delims=," %%p in ('tasklist /fi "imagename eq python.exe" /fo csv /nh 2^>nul') do (
    rem 仅提示，不做强杀，避免误伤其它 python 任务
)
echo  [1/3] 检查数据源...

rem ---- ROS 桥接（走网线，8770）----
netstat -ano | findstr ":8770 " >nul
if errorlevel 1 (
    start "ros_bridge" /min "%PY%" "%~dp0ros_bridge.py" --port 8770
    echo       ROS 桥接已启动  ^(端口 8770 ^)
) else (
    echo       ROS 桥接已在运行  ^(端口 8770 ^)
)

rem ---- CAN 桥接（走 USB 分析仪，8780）----
netstat -ano | findstr ":8780 " >nul
if errorlevel 1 (
    start "can_bridge" /min "%PY%" "%~dp0can_bridge.py" --port 8780
    echo       CAN 桥接已启动  ^(端口 8780 ^)
) else (
    echo       CAN 桥接已在运行  ^(端口 8780 ^)
)

echo.
echo  [2/3] 等待桥接就绪...
timeout /t 4 /nobreak >nul

echo.
echo  [3/3] 检查连通性
call :probe 8770 "ROS  ^(网线 / 车机 192.168.1.102^)"
call :probe 8780 "CAN  ^(USB 分析仪^)"

echo.
echo ------------------------------------------------------------
echo   看板地址 : http://127.0.0.1:8780/
echo   或直接打开页面文件
echo ------------------------------------------------------------
echo.
set /p OPEN=是否现在打开看板？(Y/N) 
if /i "%OPEN%"=="Y" start "" "http://127.0.0.1:8780/"

echo.
echo  （本窗口可关闭，桥接在后台继续运行）
timeout /t 5 /nobreak >nul
exit /b

:probe
powershell -NoProfile -Command "try{ $r=Invoke-RestMethod 'http://127.0.0.1:%~1/api/meta' -TimeoutSec 4; Write-Host '       %~2  ->  在线' }catch{ Write-Host '       %~2  ->  未连通（检查设备/网线）' }"
exit /b
