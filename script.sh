#!/bin/bash

# Matar processos antigos

# Encerra todas as instâncias do Gazebo
pkill -9 gzserver
pkill -9 gzclient

# Encerra todas as instâncias do PX4
pkill -9 px4

# Confirmação
sleep 1
pkill -x px4 || true
pkill -x gzserver || true
pkill -x gzclient || true

# Iniciar o primeiro PX4 (Drone) em uma nova aba
gnome-terminal --tab --title="PX4 Drone 1" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 ./build/px4_sitl_default/bin/px4 -i 1; exec bash'

# Esperar o Gazebo abrir para evitar problemas
sleep 10

# Iniciar o segundo PX4 (Avião) em outra nova aba
gnome-terminal --tab --title="PX4 Drone 2" -- bash -c 'cd ~/PX4-Autopilot && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE="0,2" PX4_SIM_MODEL=gz_x500_mono_cam ./build/px4_sitl_default/bin/px4 -i 2; exec bash'

# Abrir o QGroundControl em uma terceira nova aba
gnome-terminal --tab --title="QGroundControl" -- bash -c 'cd ~ && ./QGroundControl.AppImage; exec bash'

# Esperar QGroundControl abrir
sleep 10

#rodar script em python
python3 ~/multivehicle/mavsdk_drone_show-0.2/offboard_multiple_from_csv_TEST.py
