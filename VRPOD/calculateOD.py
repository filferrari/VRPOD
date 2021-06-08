from random import uniform
from Plot import draw_routes
from Utilities import Instance
from VRPOD import solve_VRPOD
from math import sqrt
import pandas as pd


import SolomonLibReader


solomon = "solomon 50.xlsx"
od_destinations = SolomonLibReader.od_destinations(25, solomon)



with open("OD_Des50.txt", "w") as file:
    file.write(str(od_destinations))


