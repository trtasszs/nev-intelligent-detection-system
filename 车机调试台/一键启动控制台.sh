#!/bin/bash
# ============================================================
#  一键启动控制台（由 Windows 侧「一键启动车机调试.bat」调用）
#  作用：自动找到 X 会话授权文件，然后在图形会话里拉起车机调试台
# ============================================================

export DISPLAY=:0

# 自动定位 XAUTHORITY（不同登录方式路径不同）
for xa in /run/user/1000/gdm/Xauthority \
          "$HOME/.Xauthority" \
          /run/user/1000/Xauthority \
          /run/user/1000/gdm/Xauthority; do
    if [ -f "$xa" ]; then
        export XAUTHORITY="$xa"
        break
    fi
done

source /opt/ros/melodic/setup.bash 2>/dev/null
export ROS_MASTER_URI=http://192.168.1.102:11311
export ROS_IP=192.168.1.109
export ROS_HOSTNAME=192.168.1.109

echo "[启动器] DISPLAY=$DISPLAY  XAUTHORITY=$XAUTHORITY"

# 关掉旧实例，避免多个窗口
pkill -f '车机调试台.py' 2>/dev/null
sleep 1

nohup python2 "/home/pji/xk/车机调试台.py" > /tmp/center.log 2>&1 &
sleep 2

if pgrep -f '车机调试台.py' >/dev/null; then
    echo "[启动器] 车机调试台已启动 (PID $(pgrep -f '车机调试台.py' | head -1))"
else
    echo "[启动器] 启动失败，日志："
    cat /tmp/center.log 2>/dev/null | tail -20
fi
