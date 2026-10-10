@echo off
chcp 65001 >nul
title 激光雷达 - 放开数据端口（需要管理员）
setlocal EnableDelayedExpansion

rem ============================================================
rem  自查：当前是否管理员，不是就用 UAC 提权重启本脚本
rem  ASCII-only comments on purpose (see project notes)
rem ============================================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   需要管理员权限，正在请求提权...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo   激光雷达 - 放开 UDP 数据端口
echo ============================================================
echo.
echo   问题: Windows 防火墙三个配置都是 BlockInbound,AllowOutbound
echo         雷达的 MSOP(2368) / DIFOP(7788) 属于「非请求入站 UDP」,
echo         默认会被静默丢弃 —— 表现为 ping 得通但收不到任何数据。
echo.
echo   本脚本将放行以下 UDP 入站端口:
echo         2368 2369 2370 2371 2372   (MSOP 点云数据)
echo         7788 7789 7790 7791 7792   (DIFOP 设备信息)
echo.

rem ---- 先删同名旧规则，避免重复 ----
netsh advfirewall firewall delete rule name="LeiShen Lidar MSOP (UDP-In)" >nul 2>&1
netsh advfirewall firewall delete rule name="LeiShen Lidar DIFOP (UDP-In)" >nul 2>&1

rem ---- 放行 MSOP ----
netsh advfirewall firewall add rule ^
    name="LeiShen Lidar MSOP (UDP-In)" ^
    dir=in action=allow protocol=UDP ^
    localport=2368,2369,2370,2371,2372 ^
    profile=any ^
    description="LeiShen lidar MSOP point cloud data"
if errorlevel 1 ( echo   [x] MSOP 规则添加失败 ) else ( echo   [OK] 已放行 MSOP  2368-2372 )

rem ---- 放行 DIFOP ----
netsh advfirewall firewall add rule ^
    name="LeiShen Lidar DIFOP (UDP-In)" ^
    dir=in action=allow protocol=UDP ^
    localport=7788,7789,7790,7791,7792 ^
    profile=any ^
    description="LeiShen lidar DIFOP device info"
if errorlevel 1 ( echo   [x] DIFOP 规则添加失败 ) else ( echo   [OK] 已放行 DIFOP 7788-7792 )

echo.
echo ------------------------------------------------------------
echo   附加项: 雷达的「目标 IP」是出厂配死的，不是本机 .109。
echo   实测证据: 静默 15 秒网卡只收到 12 个广播小包(60 字节),
echo             单播 = 0 —— 雷达一直在广播找一个不存在的地址,
echo             没人应答, 它就永远不发点云数据。
echo   镭神雷达 IP 为 192.168.1.200 时, 配套主机地址通常是
echo   192.168.1.102。下面给「以太网」加这个第二 IP,
echo   不影响原有的 192.168.1.109。
echo ------------------------------------------------------------
echo.
set /p ADDIP=是否添加第二 IP 192.168.1.102 ？(Y/N，直接回车=Y) 
if /i "%ADDIP%"=="" set "ADDIP=Y"
if /i "%ADDIP%"=="Y" (
    netsh interface ipv4 add address "以太网" 192.168.1.102 255.255.255.0 >nul 2>&1
    if errorlevel 1 (
        echo   [x] 添加失败 —— 可能已存在
    ) else (
        echo   [OK] 已添加 192.168.1.102/24
    )
    echo.
    echo   如果加了还是收不到，把下面这个也加上（镭神另一套常见默认）:
    echo       netsh interface ipv4 add address "以太网" 192.168.1.222 255.255.255.0
    echo   撤销命令:
    echo       netsh interface ipv4 delete address "以太网" 192.168.1.102
    echo       netsh interface ipv4 delete address "以太网" 192.168.1.222
)

echo.
echo ============================================================
echo   完成。现在可以回到主会话重新抓包了。
echo   验证命令:
echo     python "E:\！！！高职比赛\车机实时数据\lidar_udp.py" --probe --secs 6
echo ============================================================
echo.
pause
endlocal
