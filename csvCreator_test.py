import csv
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
from functions.export_and_plot_shape import export_and_plot_shape
from functions.trajectories import *
from functions.create_active_csv import create_active_csv

def create_active_csv_plane(shape_name, diameter, direction, maneuver_time, start_x, start_y, initial_altitude, climb_rate, move_speed, hold_time, step_time, output_file):
    # Função adaptada para gerar um CSV específico para o avião
    create_active_csv(
        shape_name=shape_name,
        diameter=diameter,
        direction=direction,
        maneuver_time=maneuver_time,
        start_x=start_x,
        start_y=start_y,
        initial_altitude=initial_altitude,
        climb_rate=climb_rate,
        move_speed=move_speed,
        hold_time=hold_time,
        step_time=step_time,
        output_file=output_file,
    )

# Configurações para o drone
shape_name = "heart_shape"
diameter = 30.0
direction = 1
maneuver_time = 90.0
start_x = 0
start_y = 0
initial_altitude = 15
climb_rate = 1.0
move_speed = 2.0
hold_time = 4.0
step_time = 0.1

output_file_drone = "shapes/active.csv"
create_active_csv(
    shape_name=shape_name,
    diameter=diameter,
    direction=direction,
    maneuver_time=maneuver_time,
    start_x=start_x,
    start_y=start_y,
    initial_altitude=initial_altitude,
    climb_rate=climb_rate,
    move_speed=move_speed,
    hold_time=hold_time,
    step_time=step_time,
    output_file=output_file_drone,
)
export_and_plot_shape(output_file_drone)

# Configurações para o avião de asa fixa
output_file_plane = "shapes/active_plane.csv"
create_active_csv_plane(
    shape_name="circle",
    diameter=50.0,
    direction=1,
    maneuver_time=120.0,
    start_x=10,
    start_y=10,
    initial_altitude=20,
    climb_rate=0.5,
    move_speed=5.0,
    hold_time=6.0,
    step_time=0.1,
    output_file=output_file_plane,
)
export_and_plot_shape(output_file_plane)
