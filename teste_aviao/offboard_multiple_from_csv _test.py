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

global_position_telemetry = {}

def start_mavsdk_server(port, udp_port):
    print(f"Starting mavsdk_server on port {port} for UDP {udp_port}")
    return subprocess.Popen(["./mavsdk_server", "-p", str(port), f"udp://:{udp_port}"])

async def get_global_position_telemetry(drone_id, drone):
    async for global_position in drone.telemetry.position():
        global_position_telemetry[drone_id] = global_position
        break

async def run_vehicle(drone_id, trajectory_offset, udp_port, time_offset, altitude_offset, csv_file):
    grpc_port = 50040 + drone_id
    vehicle = System(mavsdk_server_address="127.0.0.1", port=grpc_port)
    await asyncio.sleep(2)  # Dar tempo para iniciar
    
    print(f"Connecting vehicle {drone_id} to UDP: {udp_port}")
    await vehicle.connect(system_address=f"udp://:{udp_port}")
    asyncio.ensure_future(get_global_position_telemetry(drone_id, vehicle))
    await asyncio.sleep(time_offset)

    # Esperar até a conexão ser estabelecida
    connected = False
    for _ in range(20):  # Tentar por 20 segundos
        async for state in vehicle.core.connection_state():
            if state.is_connected:
                print(f"Vehicle {drone_id} connected on UDP {udp_port} and gRPC {grpc_port}")
                connected = True
                break
        if connected:
            break
        print(f"Waiting for connection on UDP {udp_port}...")
        await asyncio.sleep(1)
    if not connected:
        print(f"ERROR: Vehicle {drone_id} failed to connect on UDP {udp_port}")
        return

    async for health in vehicle.telemetry.health():
        if health.is_global_position_ok:
            print(f"Global position estimate OK for vehicle {drone_id}")
            break

    print(f"-- Arming vehicle {drone_id}")
    await vehicle.action.arm()
    print(f"-- Setting initial setpoint for vehicle {drone_id}")
    await vehicle.offboard.set_position_ned(PositionNedYaw(0.0, 0.0, 0.0, 0.0))
    
    print(f"-- Starting offboard for vehicle {drone_id}")
    try:
        await vehicle.offboard.start()
    except OffboardError as e:
        print(f"ERROR: Offboard mode start failed for vehicle {drone_id}: {e}")
        print(f"-- Disarming vehicle {drone_id}")
        await vehicle.action.disarm()
        return

    waypoints = []
    with open(csv_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            waypoints.append(
                (
                    float(row["t"]), float(row["px"]) + trajectory_offset[0],
                    float(row["py"]) + trajectory_offset[1],
                    float(row["pz"]) + trajectory_offset[2] - altitude_offset,
                    float(row["vx"]), float(row["vy"]), float(row["vz"]),
                    float(row["ax"]), float(row["ay"]), float(row["az"]),
                    float(row["yaw"])
                )
            )

    print(f"-- Performing trajectory for vehicle {drone_id}")
    total_duration = waypoints[-1][0]
    t = 0
    while t <= total_duration:
        current_waypoint = next((wp for wp in waypoints if t <= wp[0]), None)
        if not current_waypoint:
            break

        position = current_waypoint[1:4]
        velocity = current_waypoint[4:7]
        acceleration = current_waypoint[7:10]
        yaw = current_waypoint[-1]

        await vehicle.offboard.set_position_velocity_acceleration_ned(
            PositionNedYaw(*position, yaw),
            VelocityNedYaw(*velocity, yaw),
            AccelerationNed(*acceleration)
        )
        await asyncio.sleep(0.1)
        t += 0.1

    print(f"-- Landing vehicle {drone_id}")
    await vehicle.action.land()
    async for state in vehicle.telemetry.landed_state():
        if state == LandedState.ON_GROUND:
            break

    print(f"-- Stopping offboard for vehicle {drone_id}")
    try:
        await vehicle.offboard.stop()
    except Exception:
        pass

    print(f"-- Disarming vehicle {drone_id}")
    await vehicle.action.disarm()

async def main():
    udp_ports = [14540, 14541]
    csv_files = ["shapes/active_test.csv", "shapes/active_plane.csv"]
    mavsdk_servers = []
    for i in range(2):
        mavsdk_servers.append(start_mavsdk_server(50040 + i, udp_ports[i]))
    
    await asyncio.sleep(5)  # Esperar servidores iniciarem
    
    tasks = []
    for i in range(2):
        print(f"Starting vehicle {i} on UDP port {udp_ports[i]}")
        tasks.append(asyncio.create_task(run_vehicle(i, (0, 3*i, 0), udp_ports[i], i, 0, csv_files[i])))
    await asyncio.gather(*tasks)

    for server in mavsdk_servers:
        server.terminate()
        server.wait()
    
    print("All vehicles completed execution.")

if __name__ == "__main__":
    asyncio.run(main())
