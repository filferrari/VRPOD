from typing import Dict, List, Tuple
from dataclasses import dataclass
from random import uniform
from Plot import draw_routes
from Utilities import Instance, distance_toll, distance_toll_access
from VRPOD import solve_VRPOD
from VRPOD_RA import solve_VRPOD_RA
from VRPOD_RA_access import solve_VRPOD_access
from Savings import heuristic
from Saving_access import heuristic_access
from Saving_dist import heuristic_dist
from Sweep import heuristic_sweep
from Sweep_access import heuristic_sweep_access
from Sweep_dist import heuristic_sweep_dist
from math import sqrt
from shapely.geometry import LineString
import shapely

# (1) read instance data
import SolomonLibReader

solomon = "solomon 25.xlsx"
#solomon = "solomon 50.xlsx"
#solomon= "solomon 100.xlsx"
data = SolomonLibReader.read(solomon)

# (2) create instance
C = data["c"]
T = 0.2
#T = 0.5
#T = 1   # tax for unit of distance inside RA, used in distance based toll model
#T_access = 1    # lump tax paid once the RA is accessed, used in access based toll model
#T_access = 5
T_access = 5
K =15
#K = 15
#K =10
#K =20
Q = 200
max_dev = 1.2
rho = 1.4
#rho=2
CF = 1
with open("OD_Des25.txt", "r") as file:
    od_destinations = eval(file.readline())
nodes = data["nodes"][:] + od_destinations
nodesRD = data["nodes"][:]
nodesRD_WD = data["nodes"][:]
nodesRD_WD.pop(0)

#l = [50,50,50,50,50]
#l = [50,50,50,50,50,50,50,50,50,50]
#l = [50,50,50,50,50,50,50,50,50,50,50,50,50,50,50]
l = [50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50]
#l = [50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50,50]

#m = [25,25,25,25,25]
#m = [25,25,25,25,25,25,25,25,25,25]
#m = [25,25,25,25,25,25,25,25,25,25,25,25,25,25,25]
m = [25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25]
#m = [25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25,25]


#v = [1,1,1,1,1]
#v = [1,1,1,1,1,1,1,1,1,1]
v = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
#v = [1,0,1,1,0,1,1,0,1,0,1,1,1,1,0,1]
#v = [0,0,1,0,1,0,0,1,0,1,0,0,0,1,0]

t_access = dict()  # t for pay-per-entry toll
for n_from in nodes:
    for n_to in nodes:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        if n_from == n_to:
            t_access[n_from["id"], n_to["id"]] = 1000
        elif distance_toll_access((x_from, y_from), (x_to, y_to)):
            t_access[n_from["id"], n_to["id"]] = 1
        else:
            t_access[n_from["id"], n_to["id"]] = 0

t = dict()  # t for distance-based toll
for n_from in nodes:
    for n_to in nodes:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        if n_from == n_to:
            t[n_from["id"], n_to["id"]] = 1000
        else:
            t[n_from["id"], n_to["id"]] = distance_toll((x_from, y_from), (x_to, y_to))

q = list()
for node in data["nodes"]:
    q.append(node["demand"])

d = dict()
for n_from in nodes:
    for n_to in nodes:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        if n_from == n_to:
            d[n_from["id"], n_to["id"]] = 1000
        else:
            d[n_from["id"], n_to["id"]] = sqrt((x_from - x_to) ** 2 + (y_from - y_to) ** 2)

dRD = dict()
for n_from in nodesRD:
    for n_to in nodesRD:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        if n_from == n_to:
            dRD[n_from["id"], n_to["id"]] = 1000
        else:
            dRD[n_from["id"], n_to["id"]] = sqrt((x_from - x_to) ** 2 + (y_from - y_to) ** 2)

dRD_WD = dict()
for n_from in nodesRD_WD:
    for n_to in nodesRD_WD:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        if n_from == n_to:
            dRD_WD[n_from["id"], n_to["id"]] = 1000
        else:
            dRD_WD[n_from["id"], n_to["id"]] = sqrt((x_from - x_to) ** 2 + (y_from - y_to) ** 2)


#goaround
def dist(n_from, n_to):
    x_from = n_from["x"]
    x_to = n_to["x"]
    y_from = n_from["y"]
    y_to = n_to["y"]
    if n_from == n_to:
        d=  1000
    else:
        d = sqrt((x_from - x_to) ** 2 + (y_from - y_to) ** 2)
    return d

#distance matrices for distance toll

d_dist = d.copy()
dcorner_dist = dict()
for n_from in nodes:
    for n_to in nodes:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        corner1 = {"id": 1, "x": 35, "y": 35}
        corner2 = {"id": 2, "x": 70, "y": 35}
        corner3 = {"id": 3, "x": 70, "y": 70}
        corner4 = {"id": 4, "x": 35, "y": 70}
        ra = LineString([(35, 70), (35, 35), (70, 35)])
        line1 = LineString([(x_from, y_from), (x_to, y_to)])
        intercept = line1.intersection(ra)

        minprice = d_dist[n_from["id"], n_to["id"]] + t[n_from["id"], n_to["id"]] * T * d_dist[n_from["id"], n_to["id"]]
        minroute = [n_from, n_to]
        if type(intercept) is shapely.geometry.multipoint.MultiPoint:
            intercept1 = intercept[0].x, intercept[0].y
            intercept2 = intercept[1].x, intercept[1].y


            #minprice = d[n_from, n_to]+t[n_from, n_to]*T*d[n_from, n_to]
            #minroute=[n_from, n_to]
            if dist(n_from, corner1) + dist(corner1, n_to) + distance_toll((x_from, y_from),(corner1["x"], corner1["y"])) * T * dist(n_from, corner1) + distance_toll((corner1["x"], corner1["y"]), (x_to, y_to)) * T * dist(corner1,n_to) < minprice:
                minprice = dist(n_from, corner1) + dist(corner1, n_to) + distance_toll((x_from, y_from), (corner1["x"], corner1["y"])) * T * dist(n_from, corner1) + distance_toll((corner1["x"], corner1["y"]),(x_to, y_to)) * T * dist(corner1, n_to)
                minroute = [n_from, corner1, n_to]
            if dist(n_from, corner2) + dist(corner2, n_to) + distance_toll((x_from, y_from),(corner2["x"], corner2["y"])) * T * dist(n_from, corner2) + distance_toll((corner2["x"], corner2["y"]), (x_to, y_to)) * T * dist(corner2,n_to) < minprice:
                minprice = dist(n_from, corner2) + dist(corner2, n_to) + distance_toll((x_from, y_from), (corner2["x"], corner2["y"])) * T * dist(n_from, corner2) + distance_toll((corner2["x"], corner2["y"]),(x_to, y_to)) * T * dist(corner2, n_to)
                minroute = [n_from,corner2, n_to]
            if dist(n_from, corner3) + dist(corner3, n_to) + distance_toll((x_from, y_from),(corner3["x"], corner3["y"])) * T * dist(n_from, corner3) + distance_toll((corner3["x"], corner3["y"]), (x_to, y_to)) * T * dist(corner3,n_to) < minprice:
                minprice = dist(n_from, corner3) + dist(corner3, n_to) + distance_toll((x_from, y_from), (corner3["x"], corner3["y"])) * T * dist(n_from, corner3) + distance_toll((corner3["x"], corner3["y"]), (x_to, y_to)) * T * dist(corner3, n_to)
                minroute = [n_from,corner3, n_to]
            if dist(n_from, corner4) + dist(corner4, n_to) + distance_toll((x_from, y_from),(corner4["x"], corner4["y"])) * T * dist(n_from, corner4) + distance_toll((corner4["x"], corner4["y"]), (x_to, y_to)) * T * dist(corner4, n_to) < minprice:
                minprice = dist(n_from, corner4) + dist(corner4, n_to) + distance_toll((x_from, y_from), (corner4["x"], corner4["y"])) * T * dist(n_from, corner4) + distance_toll((corner4["x"], corner4["y"]),(x_to, y_to)) * T * dist(corner4, n_to)
                minroute = [n_from, corner4, n_to]
        if len(minroute) == 3:
            dcorner_dist[n_from["id"], n_to["id"]]=minroute[1]
            """print("before")
            print(d_dist[n_from["id"], n_to["id"]])
            print(t[n_from["id"], n_to["id"]])"""
            d_dist[n_from["id"], n_to["id"]] = dist(n_from,minroute[1])+dist(minroute[1],n_to)
            t[n_from["id"], n_to["id"]] = (distance_toll((x_from, y_from),(minroute[1]["x"], minroute[1]["y"]))*dist(n_from,minroute[1])+distance_toll((minroute[1]["x"], minroute[1]["y"]), (x_to, y_to))*dist(minroute[1],n_to))/(dist(n_from,minroute[1])+dist(minroute[1],n_to))
            """print("after")
            print(d_dist[n_from["id"], n_to["id"]])
            print(t[n_from["id"], n_to["id"]])"""
        else:
            dcorner_dist[n_from["id"], n_to["id"]]=0

#distance matrix access toll

d_access = d.copy()
dcorner_access = dict()
for n_from in nodes:
    for n_to in nodes:
        x_from = n_from["x"]
        x_to = n_to["x"]
        y_from = n_from["y"]
        y_to = n_to["y"]
        corner1 = {"id": 1, "x": 35, "y": 35}
        corner2 = {"id": 2, "x": 70, "y": 35}
        corner3 = {"id": 3, "x": 70, "y": 70}
        corner4 = {"id": 4, "x": 35, "y": 70}
        ra = LineString([(35, 70), (35, 35), (70, 35)])
        line1 = LineString([(x_from, y_from), (x_to, y_to)])
        intercept = line1.intersection(ra)

        minprice = d_dist[n_from["id"], n_to["id"]] + t_access[n_from["id"], n_to["id"]] * T_access
        minroute = [n_from, n_to]
        if type(intercept) is shapely.geometry.multipoint.MultiPoint:
            intercept1 = intercept[0].x, intercept[0].y
            intercept2 = intercept[1].x, intercept[1].y



            if dist(n_from, corner1) + dist(corner1, n_to) + distance_toll_access((x_from, y_from),(corner1["x"], corner1["y"])) * T_access + distance_toll_access((corner1["x"], corner1["y"]), (x_to, y_to)) * T_access < minprice:
                minprice = dist(n_from, corner1) + dist(corner1, n_to) + distance_toll_access((x_from, y_from), (corner1["x"], corner1["y"])) * T_access + distance_toll_access((corner1["x"], corner1["y"]),(x_to, y_to)) * T_access
                minroute = [n_from, corner1, n_to]
            if dist(n_from, corner2) + dist(corner2, n_to) + distance_toll_access((x_from, y_from),(corner2["x"], corner2["y"])) * T_access + distance_toll_access((corner2["x"], corner2["y"]), (x_to, y_to)) * T_access < minprice:
                minprice = dist(n_from, corner2) + dist(corner2, n_to) + distance_toll_access((x_from, y_from), (corner2["x"], corner2["y"])) * T_access + distance_toll_access((corner2["x"], corner2["y"]),(x_to, y_to)) * T_access
                minroute = [n_from,corner2, n_to]
            if dist(n_from, corner3) + dist(corner3, n_to) + distance_toll_access((x_from, y_from),(corner3["x"], corner3["y"])) * T_access + distance_toll_access((corner3["x"], corner3["y"]), (x_to, y_to)) * T_access < minprice:
                minprice = dist(n_from, corner3) + dist(corner3, n_to) + distance_toll_access((x_from, y_from), (corner3["x"], corner3["y"])) * T_access + distance_toll_access((corner3["x"], corner3["y"]), (x_to, y_to)) * T_access
                minroute = [n_from,corner3, n_to]
            if dist(n_from, corner4) + dist(corner4, n_to) + distance_toll_access((x_from, y_from),(corner4["x"], corner4["y"])) * T_access + distance_toll_access((corner4["x"], corner4["y"]), (x_to, y_to)) * T_access < minprice:
                minprice = dist(n_from, corner4) + dist(corner4, n_to) + distance_toll_access((x_from, y_from), (corner4["x"], corner4["y"])) * T_access + distance_toll_access((corner4["x"], corner4["y"]),(x_to, y_to)) * T_access
                minroute = [n_from, corner4, n_to]
        if len(minroute) == 3:
            dcorner_access[n_from["id"], n_to["id"]]=minroute[1]
            """print("before")
            print(d_access[n_from["id"], n_to["id"]])
            print(t_access[n_from["id"], n_to["id"]])"""
            d_access[n_from["id"], n_to["id"]] = dist(n_from,minroute[1])+dist(minroute[1],n_to)
            t_access[n_from["id"], n_to["id"]] = (distance_toll_access((x_from, y_from),(minroute[1]["x"], minroute[1]["y"]))+distance_toll_access((minroute[1]["x"], minroute[1]["y"]), (x_to, y_to)))
            """print("after")
            print(d_access[n_from["id"], n_to["id"]])
            print(t_access[n_from["id"], n_to["id"]])"""
        else:
            dcorner_access[n_from["id"], n_to["id"]]=0




#print(dcorner_access)
#print(dcorner_dist)
print("Customers:", C)
print("ODs:", K)
print("RD vehicle capacity:", Q)
print("Toll:", T)
print("Max detour length:", max_dev)
print("Compensation factor OD:", rho)
print("Cost factor Rd:", CF)
print("Nodes:", nodes)
print("Demand RD:", q)
print("Demand OD:", m)
print("Capacity of OD vehicle:", l)
print("OD Vehicle applicable to toll:", v)
"""print("Toll indicator:", t)
print("Distances1:", d)
print("Distances2:", dRD)
print("Distances3:", dRD_WD)"""


instance = Instance(C, K, Q, T_access, max_dev, rho, CF, nodes, nodesRD, nodesRD_WD, q, m, l, v, t_access, d, d, dRD, dRD_WD, dcorner_access,t)
#print(instance)
instance_access = Instance(C, K, Q, T_access, max_dev, rho, CF, nodes, nodesRD, nodesRD_WD, q, m, l, v, t_access, d, d_access, dRD, dRD_WD, dcorner_access,t)
#print (instance_access)
dcorner=dcorner_dist.copy()
instance_dist = Instance(C, K, Q, T, max_dev, rho, CF, nodes, nodesRD, nodesRD_WD, q, m, l, v, t, d, d_dist, dRD, dRD_WD, dcorner_dist,t)
#print (instance_dist)


# Results
solution = solve_VRPOD(instance=instance)
solution_toll_access = solve_VRPOD_access(instance=instance_access)
solution_toll = solve_VRPOD_RA(instance=instance_dist)

print("\n------------------------------------ KPIs ------------------------------------\n")

print("\n----- ORIGNAL VRPOD FORMULATION -----")
if type(solution) == str:
    print(solution)
else:
    RD_routes, costs, rd_costs, od_compensation, customers_rd, customers_od, distance_rd, distance_od = solution

    OD_routes = list()
    for (i, j) in customers_od:
        OD_routes.append([0, i, j])
    routes = RD_routes + OD_routes
    draw_routes(routes, instance)

    total_distance_covered = distance_rd + distance_od

    print('Total delivery costs:', costs)
    print('RD costs: ', rd_costs)
    print('OD compensations: ', od_compensation)
    print('Total distance: ', total_distance_covered)
    print('Distance covered by RD: ', distance_rd)
    print("Number of customers served by the RD: ", len(customers_rd))
    print('Number of customers served by ODs: ', len(customers_od))
    print('Number of RD tours: ', len(RD_routes))
    print("Tours:", RD_routes)


print("\n----- VRPOD WITH PAY-PER-ENTRY TOLL SCHEME -----")
if type(solution_toll_access) == str:
    print(solution_toll_access)
else:
    RD_routes_ta, costs_ta, rd_costs_ta, od_compensation_ta, customers_rd_ta, customers_od_ta, distance_rd_ta, distance_od_ta, rd_timestoll, od_timestoll ,rd_distance_RA_ta, od_distance_RA_ta= solution_toll_access

    OD_routes_ta = list()
    for (i, j) in customers_od_ta:
        OD_routes_ta.append([0, i, j])

    routes_ta = RD_routes_ta + OD_routes_ta
    draw_routes(routes_ta, instance)

    #testR = [[0, 1, 9, 20, 10, 19, 8, 18, 0], [0, 6, 5, 17, 16, 14, 15, 2, 21, 22, 23, 4, 11, 26, 24, 12, 0], [0, 3, 27],[0, 7, 25], [0, 13, 30]]
    #draw_routes(testR, instance_access)

    total_distance_covered_ta = distance_rd_ta + distance_od_ta
    toll_cost_rd_ta = rd_timestoll * T_access
    toll_cost_od_ta = od_timestoll * T_access
    total_toll_cost_ta = toll_cost_od_ta + toll_cost_rd_ta

    print('Total delivery costs:', costs_ta)
    print('RD costs: ', rd_costs_ta)
    print('OD compensations: ', od_compensation_ta)
    print('Total toll costs: ', total_toll_cost_ta)
    print('Number of times toll is payed by RD: ', rd_timestoll)
    print('RD toll costs: ', toll_cost_rd_ta)
    print('ODs toll costs: ', toll_cost_od_ta)
    print('Total distance: ', total_distance_covered_ta)
    print('Distance covered by RD: ', distance_rd_ta)
    print('Distance covered by OD: ', distance_od_ta)
    print('Distance covered by RD in RA: ', rd_distance_RA_ta)
    print('Distance covered by OD in RA: ', od_distance_RA_ta)
    print("Number of customers served by the RD: ", len(customers_rd_ta))
    print('Number of customers served by ODs: ', len(customers_od_ta))
    print('Number of RD tours: ', len(RD_routes_ta))
    print("Tours:", RD_routes_ta)



print("\n----- VRPOD WITH DISTANCE-BASED TOLL SCHEME -----")

if type(solution_toll) == str:
    print(solution_toll)
else:
    RD_routes_t, costs_t, rd_costs_t, od_compensation_t, customers_rd_t, customers_od_t, distance_rd_t, distance_od_t, rd_distance_RA, od_distance_RA = solution_toll

    OD_routes_t = list()
    for (i, j) in customers_od_t:
        OD_routes_t.append([0, i, j])

    routes_t = RD_routes_t + OD_routes_t
    draw_routes(routes_t, instance_dist)

    total_distance_covered_t = distance_rd_t + distance_od_t
    toll_cost_rd_t = rd_distance_RA * T
    toll_cost_od_t = od_distance_RA * T
    total_toll_cost_t = toll_cost_od_t + toll_cost_rd_t

    print('Total delivery costs:', costs_t)
    print('RD costs: ', rd_costs_t)
    print('OD compensations: ', od_compensation_t)
    print('Total toll costs: ', total_toll_cost_t)
    print('RD toll costs: ', toll_cost_rd_t)
    print('ODs toll costs: ', toll_cost_od_t)
    print('Total distance: ', total_distance_covered_t)
    print('Distance covered by RD: ', distance_rd_t)
    print('Distance covered by OD: ', distance_od_t)
    print('Distance covered by the RD inside the RA: = ', rd_distance_RA)
    print('Distance covered by the OD inside the RA: = ', od_distance_RA)
    print("Number of customers served by the RD: ", len(customers_rd_t))
    print('Number of customers served by ODs: ', len(customers_od_t))
    print('Number of RD tours: ', len(RD_routes_t))
    print("Tours:", RD_routes_t)


print("\n----- HEURISTIC S -----------------------------------")

print("\n----- HEURISTIC S - ORIGINAL-----")
solution_heuristic = heuristic(instance = instance)
draw_routes(solution_heuristic, instance)

print("\n----- HEURISTIC S - PAY-PER-ENTRY TOLL SCHEME-----")
solution_heuristic_access = heuristic_access(instance = instance_access)
draw_routes(solution_heuristic_access, instance_access)

print("\n----- HEURISTIC S - DISTANCE-BASED TOLL SCHEME-----")
solution_heuristic_dist = heuristic_dist(instance = instance_dist)
draw_routes(solution_heuristic_dist, instance_dist)

print("\n----- HEURISTIC S* -----------------------------------")

print("\n----- HEURISTIC S* - ORIGINAL-----")
solution_heuristic_sweep = heuristic_sweep(instance=instance)
draw_routes(solution_heuristic_sweep, instance)

print("\n----- HEURISTIC S* - PAY-PER-ENTRY TOLL SCHEME-----")
solution_heuristic_sweep_access = heuristic_sweep_access(instance=instance_access)
draw_routes(solution_heuristic_sweep_access, instance_access)

print("\n----- HEURISTIC S* - DISTANCE-BASED TOLL SCHEME-----")
solution_heuristic_sweep_dist = heuristic_sweep_dist(instance=instance_dist)
draw_routes(solution_heuristic_sweep_dist, instance_dist)