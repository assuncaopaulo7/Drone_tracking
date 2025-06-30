import os
import asyncio
from mavsdk import System
import csv
from mavsdk.offboard import PositionNedYaw, VelocityNedYaw, AccelerationNed, OffboardError
from mavsdk.telemetry import LandedState
from mavsdk.action import ActionError
from mavsdk.telemetry import *
import subprocess
import signal
import socket
import json


global_position_telemetry = {}

# Função para obter a posição global do drone
async def get_global_position_telemetry(drone_id, drone):
    async for global_position in drone.telemetry.position():
        global_position_telemetry[drone_id] = global_position
        break

# ------------------------------------------------------------------

# Função para escutar mensagens UDP e chamar a função de callback
async def listen_udp_for_detection(udp_listen_port, detection_callback):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", udp_listen_port))
    sock.setblocking(False)

    loop = asyncio.get_event_loop()

    while True:
        try:
            # recvfrom retorna (data, addr)
            data, _ = await loop.run_in_executor(None, sock.recvfrom, 1024)
            message = json.loads(data.decode("utf-8"))
            await detection_callback(message)
        except BlockingIOError:
            # Nenhum dado disponível no momento
            await asyncio.sleep(0.05)
        except json.JSONDecodeError:
            print("❌ Mensagem recebida não é JSON válido.")
        except Exception as e:
            print(f"❌ Erro inesperado ao receber/parsing UDP: {e}")
        await asyncio.sleep(0.01)

# ------------------------------------------------------------------


# Função principal para executar o drone
async def run_drone(drone_id, trajectory_offset, udp_port, time_offset, altitude_offset):
    camera_drone_id = 2           # ID do drone que está com a câmara
    image_width = 640             # dimensões da imagem da câmara
    image_height = 480
    image_center = (image_width // 2, image_height // 2)   # centro da imagem
    pixel_to_meter = 0.01                                  # fator de conversão estimado: 100 pixels ≈ 1 metro
    image_center = (image_width // 2)
    horizontal_fov = 87                                # Largura do campo de visão horizontal da câmara em graus
    degrees_per_pixel = horizontal_fov / image_width

    grpc_port = 50040 + drone_id                           # porta gRPC para cada drone

    # Descrição dos modos de voo
    mode_descriptions = {
        0: "On the ground",
        10: "Initial climbing state",
        20: "Initial holding after climb",
        30: "Moving to start point",
        40: "Holding at start point",
        50: "Moving to maneuvering start point",
        60: "Holding at maneuver start point",
        70: "Maneuvering (trajectory)",
        80: "Holding at the end of the trajectory coordinate",
        90: "Returning to home coordinate",
        100: "Landing"
    }
    
    # Inicializa o drone com o endereço gRPC e a porta UDP
    drone = System(mavsdk_server_address="127.0.0.1", port=grpc_port)
    await drone.connect(system_address=f"udp://:{udp_port}")
    print(f"Drone connecting with UDP: {udp_port}")

    # Estado para tracking
    detection_buffer = []               # Buffer para armazenar deteções recentes
    tracking_active = False             # Flag para indicar se o tracking está ativo
    udp_listen_port = 9999              # Porta onde o tracker envia
    object_position_global = None       # Posição global do objeto detetado


    # Trata de as mensagens de deteção recebidas via UDP
    async def on_detection_message(message):
        nonlocal detection_buffer, tracking_active, object_position_global      # vareáveis externas
        print(f"🛰️ UDP: {message}")
        detected = message.get("detected", False)                               # verifica se o objeto foi detetado (True/False)
        pos = message.get("position", None)                                     # posição do objeto detetado (x, y) em píxeis       

        if detected and pos and all(p is not None for p in pos):                # Se detected for True e pos não for None:
            detection_buffer.append(True)                                           # Adicione True ao buffer de deteções
            object_position_global = pos                                            # Atualiza a posição global do objeto detetado
        else:
            detection_buffer.append(False)                                      # Se detected for False, adiciona False ao buffer de deteções     

        detection_buffer = detection_buffer[-5:]

        if detection_buffer.count(True) >= 2:                                   # Se houver ao menos 2 trues no buffer de deteções:
            if not tracking_active:
                print(f"🟢 Drone {drone_id}: MODO TRACKING ATIVADO")
            tracking_active = True                                              # Ativa o modo de tracking

    # Inicia a escuta UDP para deteções se este for o drone com a câmara
    if drone_id == camera_drone_id:
        asyncio.create_task(listen_udp_for_detection(udp_listen_port, on_detection_message))

    # Conexão do drone e obtenção da posição global
    asyncio.ensure_future(get_global_position_telemetry(drone_id, drone))
    
    await asyncio.sleep(time_offset)
    
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone id {drone_id} connected on Port: {udp_port} and grpc Port: {grpc_port}")
            break
    
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print(f"Global position estimate ok {drone_id}")
            break
    # -----------------------------------------------------------------     
    
    global_position_telemetry[drone_id] = global_position_telemetry[drone_id]
    print(f"Home Position of {drone_id} set to: {global_position_telemetry[drone_id]}")
    print(f"-- Arming {drone_id}")
    await drone.action.arm()                                                                # Arma o drone
    print(f"-- Setting initial setpoint {drone_id}")
    await drone.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))               # Define o ponto inicial do drone
    
    print(f"-- Starting offboard {drone_id}")
    try:
        await drone.offboard.start()                                                        # Inicia o modo offboard(modo de voo autônomo pelo csv)
    except OffboardError as error:
        print(f"-- Disarming {drone_id}")
        await drone.action.disarm()                                                         # Desarma o drone se falhar ao iniciar o modo offboard  
        return

    # Escolha de arquivo de trajetória com base no drone_id
    if drone_id % 2 == 0:
        trajectory_file = "shapes/active.csv"   # Trajetória para drones com ID par (drone com câmara)
    else:
        trajectory_file = "shapes/active2.csv"  # Trajetória para drones com ID ímpar

    # Lê o arquivo de trajetória e aplica os offsets
    waypoints = []
    with open(trajectory_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            t = float(row["t"])                                                 # Tempo do waypoint
            px = float(row["px"]) + trajectory_offset[0]                        # Posição x do waypoint com offset
            py = float(row["py"]) + trajectory_offset[1]                        # Posição y do waypoint com offset
            pz = float(row["pz"]) + trajectory_offset[2] - altitude_offset      # Posição z do waypoint com offset e altitude
            vx = float(row["vx"])                                               # Velocidade x do waypoint
            vy = float(row["vy"])                                               # Velocidade y do waypoint 
            vz = float(row["vz"])                                               # Velocidade z do waypoint
            ax = float(row["ax"])                                               # Aceleração x do waypoint
            ay = float(row["ay"])                                               # Aceleração y do waypoint    
            az = float(row["az"])                                               # Aceleração z do waypoint
            yaw = float(row["yaw"])                                             # Angulo Yaw do waypoint
            mode_code = int(row["mode"])                                        # Código do modo do waypoint
            
            waypoints.append((t, px, py, pz, vx, vy, vz, ax, ay, az, mode_code))

    print(f"-- Performing trajectory {drone_id}")
    total_duration = waypoints[-1][0]       # Duração total da trajetória
    t = 0                                   # Tempo atual
    last_mode = 0                           # Último modo de voo
    alpha = 0.5                             # Fator de suavização do yaw

    # Loop principal para executar a trajetória
    while t <= total_duration:
        current_waypoint = None
        for waypoint in waypoints:              # Itera sobre os waypoints
            if t <= waypoint[0]:
                current_waypoint = waypoint
                break

        if current_waypoint is None:            
            break

        position = current_waypoint[1:4]        # Posição do waypoint (px, py, pz)       
        velocity = current_waypoint[4:7]        # Velocidade do waypoint (vx, vy, vz)   
        acceleration = current_waypoint[7:10]   # Aceleração do waypoint (ax, ay, az)
        mode_code = current_waypoint[-1]        # Modo do waypoint
        
        if last_mode != mode_code:               
            print(f"Drone id: {drone_id}: Mode number: {mode_code}, Description: {mode_descriptions[mode_code]}")
            last_mode = mode_code
            
        if drone_id == camera_drone_id and tracking_active and object_position_global:  # Se for o drone com a câmara e o tracking estiver ativo:
            px, _ = object_position_global                   # Coordenada x do objeto detetado
            center_x = image_width // 2                      # Centro da imagem
            graus_por_pixel = horizontal_fov / image_width   # Graus por pixel

            desvio_px = px - center_x                         # Desvio do objeto em relação ao centro da imagem
            angulo = desvio_px * graus_por_pixel              # Converte o desvio em ângulo

            if abs(angulo) > 0.5:                                    # Se o desvio for maior que 0.5 graus, corrige o yaw
                max_angulo = 45                                      # Ângulo máximo de correção (45 graus, por exemplo)
                angulo = max(min(angulo, max_angulo), -max_angulo)
                target_yaw = yaw + angulo

                # Fator de suavização com base no desvio (0.05 a 0.5, por exemplo)
                max_alpha = 0.5
                min_alpha = 0.05
                max_desvio_px = center_x  # desvio máximo possível (metade da imagem)

                # Normaliza desvio para [0, 1] e aplica interpolação linear
                alpha = min_alpha + (max_alpha - min_alpha) * min(abs(desvio_px) / max_desvio_px, 1.0)

                # Suaviza o yaw
                new_yaw = (1 - alpha) * yaw + alpha * target_yaw

                print(f"🎯 Corrigindo yaw: desvio_px={desvio_px}, angulo={angulo:.2f}°, alpha={alpha:.2f} -> new_yaw={new_yaw:.2f}°")
            else:
                new_yaw = yaw

            await drone.offboard.set_position_velocity_acceleration_ned(    # Define a posição, velocidade e aceleração NED com o novo yaw
                PositionNedYaw(*position, new_yaw),
                VelocityNedYaw(*velocity, new_yaw),
                AccelerationNed(*acceleration)
            )
        else:
            await drone.offboard.set_position_velocity_acceleration_ned(    # Define a posição, velocidade e aceleração NED sem correção de yaw
                PositionNedYaw(*position, yaw),
                VelocityNedYaw(*velocity, yaw),
                AccelerationNed(*acceleration)
            )




        await asyncio.sleep(0.1)    
        t += 0.1  # Incrementa o tempo atual

    print(f"-- Shape completed {drone_id}")
    print(f"-- Landing {drone_id}")
    await drone.action.land()           # Inicia o pouso do drone

    async for state in drone.telemetry.landed_state():      
        if state == LandedState.ON_GROUND:
            break

    print(f"-- Stopping offboard {drone_id}")
    try:
        await drone.offboard.stop()        # Para o modo offboard
    except Exception as error:
        print(f"Stopping offboard mode failed with error: {error}")

    print(f"-- Disarming {drone_id}")
    await drone.action.disarm()             # Desarma o drone

# ------------------------------------------------------------------


async def main():
    num_drones = 3         # Número de drones
    time_offset = 1         # Tempo de offset entre os drones
    altitude_steps = 0.5    # Altitude em metros para cada drone
    altitude_offsets = [altitude_steps * i for i in range(num_drones)]  # Altitudes para cada drone
    home_positions = [(0, 3 * i, 0) for i in range(num_drones)]         # Posições iniciais dos drones
    trajectory_offsets = [(0, 0, 0) for i in range(num_drones)]         # Offsets para as trajetórias dos drones
    udp_ports = [14540 + i for i in range(num_drones)]                  # Portas UDP para cada drone

    mavsdk_servers = []
    for i in range(num_drones):                                         # Inicia o servidor MAVSDK para cada drone
        port = 50040 + i
        mavsdk_server = subprocess.Popen(["./mavsdk_server", "-p", str(port), f"udp://:{udp_ports[i]}"])
        mavsdk_servers.append(mavsdk_server)

    tasks = []
    for i in range(num_drones):
        tasks.append(asyncio.create_task(run_drone(i, trajectory_offsets[i], udp_ports[i], i * time_offset, altitude_offsets[i])))  # Inicia a tarefa para cada drone

    await asyncio.gather(*tasks)  

    for mavsdk_server in mavsdk_servers:    # Encerra o servidor MAVSDK de cada drone
        os.kill(mavsdk_server.pid, signal.SIGTERM)

    print("All tasks completed. Exiting program.")

if __name__ == "__main__":
    asyncio.run(main())