#!/bin/bash
# ============================================================
#  车机调试台 启动器  （VM 桌面「车机调试台」图标的后端）
#  集成：线控底盘调控 + 视觉传感器（相机实时画面 / 点云 / 感知）
#
#  环境要点：
#    · 车机 192.168.1.102 为 ROS Master
#    · 本 VM 经【宿主中继】对外宣称 192.168.1.109（反向通路必需）
# ============================================================

source /opt/ros/melodic/setup.bash 2>/dev/null
export ROS_MASTER_URI=http://192.168.1.102:11311
export ROS_IP=192.168.1.109
export ROS_HOSTNAME=192.168.1.109

MASTER_IP=192.168.1.102
RELAY_IP=192.168.1.109
CENTER="/home/pji/xk/车机调试台.py"

WARN=""

# ---- 1. 车机链路 ----
if ping -c 1 -W 2 $MASTER_IP >/dev/null 2>&1; then
    echo "[OK] 车机 $MASTER_IP 可达"
else
    echo "[!] 车机 $MASTER_IP 不可达"
    WARN="${WARN}① 车机不可达 ($MASTER_IP)\n   请检查：车机已开机、网线插在【机身内置网口】\n\n"
fi

# ---- 2. 宿主中继（反向通路，控制指令必需）----
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/$RELAY_IP/20000" 2>/dev/null; then
    echo "[OK] 宿主中继已监听 ($RELAY_IP:20000)"
else
    echo "[!] 宿主中继未运行"
    WARN="${WARN}② 宿主 ROS 中继未运行 ($RELAY_IP:20000)\n   请在 Windows 宿主上双击：\n   桌面\\ROS-NAT-Relay\\启动ROS中继.bat\n   （该程序已设为开机自启）\n\n"
fi

# ---- 3. 提示 ----
if [ -n "$WARN" ] && command -v zenity >/dev/null 2>&1; then
    zenity --warning --width=520 --title="车机调试台 自检" \
        --text="启动自检发现问题：\n\n${WARN}界面仍会打开，可点「重试连接」。" 2>/dev/null
fi

# ---- 4. 启动控制台 ----
if [ ! -f "$CENTER" ]; then
    echo "[错误] 找不到 $CENTER"
    command -v zenity >/dev/null 2>&1 && \
        zenity --error --text="找不到控制台程序：\n$CENTER" 2>/dev/null
    exit 1
fi

# 避免重复实例
pkill -f '车机调试台.py' 2>/dev/null
sleep 1

echo "[启动] $CENTER"
exec python2 "$CENTER"
