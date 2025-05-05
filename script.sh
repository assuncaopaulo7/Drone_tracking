#!/bin/bash

# Encerra o script se qualquer comando falhar (opcional, remova se quiser mais tolerância)
set -e

echo "Matando instâncias anteriores do Gazebo e PX4..."

# Encerra todas as instâncias do Gazebo e PX4
pkill -9 gzserver || true
pkill -9 gzclient || true
pkill -9 px4 || true

# Aguarda 1 segundo
sleep 1

# Força novamente com nomes exatos (mais seguro)
pkill -x px4 || true
pkill -x gzserver || true
pkill -x gzclient || true

echo "Iniciando PX4 Drone 1..."
gnome-terminal --tab --title="PX4 Drone 1" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i 1; exec bash'

# Espera o Gazebo carregar
sleep 10

echo "Iniciando PX4 Drone 2..."
gnome-terminal --tab --title="PX4 Drone 2" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,2" PX4_SIM_MODEL=gz_x500_mono_cam ./build/px4_sitl_default/bin/px4 -i 2; exec bash'

# Espera mais um pouco se for necessário
sleep 10

# (Opcional) Abrir o QGroundControl
# echo "Abrindo QGroundControl..."
# gnome-terminal --tab --title="QGroundControl" -- bash -c 'cd ~ && ./QGroundControl.AppImage; exec bash'

echo "Executando scripts Python..."
gnome-terminal --tab --title="Offboard Script" -- bash -c 'python3 ~/multivehicle/mavsdk_drone_show-0.2/offboard_multiple_from_csv_TEST.py; exec bash'
gnome-terminal --tab --title="OpenCV Script" -- bash -c 'python3 ~/multivehicle/mavsdk_drone_show-0.2/opencv-gazebo.py; exec bash'

# Mostrar uso da GPU em tempo real
gnome-terminal --tab --title="GPU Monitor" -- bash -c 'watch -n 1 nvidia-smi; exec bash'

echo "Setup completo!"
