import csv 
import math
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import pandas as pd
from functions.export_and_plot_shape import export_and_plot_shape
from functions.trajectories import *
from functions.create_active_csv import create_active_csv

shape_name="circle"                 # nome da forma (ex: "circle" para círculo)
diameter = 20.0                     # diâmetro da forma
direction = 1                       # direção do movimento (1 para sentido horário, -1 para anti-horário)
maneuver_time = 90.0                # tempo total do movimento (em segundos)
start_x = 10                        # coordenada X inicial
start_y = 10                        # coordenada Y inicial
initial_altitude = 15               # altitude inicial (em metros)
climb_rate = 1.0                    # taxa de subida (em metros por segundo)
move_speed = 2.0                    # velocidade de movimento (em metros por segundo)
hold_time = 4.0                     # tempo de espera ao final do movimento (em segundos)
step_time = 0.1                     # intervalo de tempo entre os pontos da trajetória (em segundos)
output_file = "shapes/active.csv"   # caminho do arquivo CSV de saída

shape_name2="square"
diameter2 = 20.0
direction2 = -1
maneuver_time2 = 90.0
start_x2 = 0
start_y2 = 0
initial_altitude2 = 15
climb_rate2 = 1.0
move_speed2 = 2.0  # m/s
hold_time2 = 4.0 #s
step_time2= 0.1 #s
output_file2 = "shapes/active2.csv"

create_active_csv(
    shape_name=shape_name,
    diameter=diameter,
    direction=direction,
    maneuver_time=maneuver_time,
    start_x=start_x,
    start_y=start_y,
    initial_altitude=initial_altitude,
    climb_rate=climb_rate,
    move_speed = move_speed,
    hold_time = hold_time,
    step_time = step_time,
    output_file = output_file,
)

create_active_csv(
    shape_name=shape_name2,
    diameter=diameter2,
    direction=direction2,
    maneuver_time=maneuver_time2,
    start_x=start_x2,
    start_y=start_y2,
    initial_altitude=initial_altitude2,
    climb_rate=climb_rate2,
    move_speed = move_speed2,
    hold_time = hold_time2,
    step_time = step_time2,
    output_file = output_file2,
)

output_file = "shapes/active.csv"
export_and_plot_shape(output_file)

output_file2 = "shapes/active2.csv"
export_and_plot_shape(output_file2)
