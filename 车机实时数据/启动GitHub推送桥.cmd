@echo off
chcp 65001 >nul
title HTTP->SOCKS5 桥（GitHub 推送用）
echo 正在启动 127.0.0.1:18080 -> socks5://127.0.0.1:10808 ...
echo 保持本窗口开着；推送完成后可直接关掉。
echo.
"C:\Users\ASUS\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" "%~dp0http_socks_bridge.py" 18080 10808
pause