#!/bin/bash
set -e

echo "Matando instâncias anteriores do Gazebo e PX4..."
pkill -9 gzserver || true
pkill -9 gzclient || true
pkill -9 px4 || true
#pkill -9 -f "gz"


# Obter resolução da tela
SCREEN_WIDTH=$(xdpyinfo | awk '/dimensions:/ {print $2}' | cut -d 'x' -f1)
SCREEN_HEIGHT=$(xdpyinfo | awk '/dimensions:/ {print $2}' | cut -d 'x' -f2)
HALF_WIDTH=$((SCREEN_WIDTH / 2))

echo "Iniciando PX4 Drone 1..."
gnome-terminal --tab --title="PX4 Drone 1" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i 1; exec bash'

sleep 10

echo "Iniciando PX4 Drone 2..."
gnome-terminal --tab --title="PX4 Drone 2" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="-1,-3" PX4_SIM_MODEL=gz_x500_mono_cam ./build/px4_sitl_default/bin/px4 -i 2; exec bash'

# Aguarda o Gazebo carregar e aparecer na tela
echo "Aguardando janela do Gazebo aparecer..."
for i in {1..20}; do
    GZ_ID=$(wmctrl -l | grep -i "gazebo" | awk '{print $1}')
    if [[ ! -z "$GZ_ID" ]]; then
        echo "Janela Gazebo detectada: $GZ_ID"
        wmctrl -ir "$GZ_ID" -e 0,$HALF_WIDTH,0,$HALF_WIDTH,$SCREEN_HEIGHT
        break
    fi
    sleep 1
done

# Abrir outros scripts
echo "Executando scripts Python..."
gnome-terminal --tab --title="Interactive Tracker" -- bash -c 'python3 ~/multivehicle/projeto_final/mavsdk_drone_show-0.2/interactive_tracker.py; exec bash'
# Esperar a janela do YOLO aparecer e movê-la para a esquerda da tela
echo "Aguardando janela do YOLO aparecer..."
for i in {1..10}; do
    YOLO_ID=$(wmctrl -l | grep -i "Ultralytics YOLO Interactive Tracking" | awk '{print $1}')
    if [[ ! -z "$YOLO_ID" ]]; then
        echo "Janela YOLO detectada: $YOLO_ID"
        wmctrl -ir "$YOLO_ID" -e 0,0,0,$HALF_WIDTH,$SCREEN_HEIGHT
        break
    fi
    sleep 1
done

gnome-terminal --tab --title="Offboard Script" -- bash -c 'python3 ~/multivehicle/projeto_final/mavsdk_drone_show-0.2/offboard_multiple_from_csv.py; exec bash'
gnome-terminal --tab --title="GPU Monitor" -- bash -c 'watch -n 1 nvidia-smi; exec bash'

echo "Setup completo!"