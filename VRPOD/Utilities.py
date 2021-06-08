from typing import Dict, List, Tuple
from dataclasses import dataclass
from shapely.geometry import LineString
import shapely
from math import sqrt


@dataclass
class Instance():
    C: int                                          # number online customers
    K: int                                          # number ODs
    Q: int                                          # RD vehicles load capacity
    T: int                                          # toll
    max_dev: float                                  # maximum detour length
    rho: float                                      # compensation factor for ODs (per distance unit of the detours)
    CF: int                                         # cost factor for ODs (per distance unit travelled)
    nodes: List                                     # vertices (depot + customers + ODs)
    nodesRD: List                                   # vertices (depot + customers)
    nodesRD_WD: List                                # vertices (customers)
    q: [int]                                        # RD demand
    m: [int]                                        # OD demand
    l: [int]                                        # OD capacity
    v: [int]                                        # OD vehicle applicable to toll
    t: Dict[Tuple[int, int], float]                 # toll on arc
    d_sd: Dict[Tuple[int, int], float]              #distance between nodes for OD without toll
    d: Dict[Tuple[int, int], float]                 # distance between nodes
    dRD: Dict[Tuple[int, int], float]               # distance between nodesRD
    dRD_WD: Dict[Tuple[int, int], float]            # distance between nodesRD_WD
    dcorner: Dict[Tuple[int, int], float]           # corner over which the ark goes
    t_dist: Dict[Tuple[int, int], float]            # dist toll fraction on arc



node = int
Arc = Tuple[int, int]
def create_tour(arcs: Dict[Arc, bool]) -> List[node]:
    nodes = sorted(set([customer_i for (customer_i, customer_j) in arcs]))
    #print(nodes)

    successors = [[]]
    while len(successors) < len(nodes):
        successors.append([])
    for (i,j) in arcs.keys():
        if arcs[i,j] == True:
            successors[i] += [j]
    #print("successors: ", successors)

    length_succ = 0
    for i in successors:
        length_succ += len(i)
    #print(length_succ)

    first_node = 0
    tour = [first_node]

    while len(tour) < length_succ:
        next_node = successors[first_node].pop(0)
        tour.append(next_node)
        first_node = next_node
    return tour

def create_routes(tour: List[int]) -> List[List[int]]:
    routes = list()
    routes.append([0])
    tour.remove(0)
    #print(routes)
    #print(tour)
    while len(tour) != 0:
        if tour[0] != 0:
            routes[-1].append(tour[0])
            tour.pop(0)
        else:
            routes[-1].append(0)
            tour.pop(0)
            routes.append([0])
        #print(len(tour))
    routes[-1].append(0)
    return routes

def distance_toll(n_out, n_in):
    ra = LineString([(35, 70), (35, 35), (70, 35)])
    line1 = LineString([n_out, n_in])
    intercept = line1.intersection(ra)

    if type(intercept) is shapely.geometry.point.Point:
        a = intercept.x, intercept.y
        if (n_out[0] <= 35 or n_out[1] <= 35) and (n_in[0] > 35 and n_in[1] > 35):
            distance_toll = sqrt((a[0] - n_in[0]) ** 2 + (a[1] - n_in[1]) ** 2)
        elif (n_in[0] <= 35 or n_in[1] <= 35) and (n_out[0] > 35 and n_out[1] > 35):
            distance_toll = sqrt((a[0] - n_out[0]) ** 2 + (a[1] - n_out[1]) ** 2)
        else:
            distance_toll = 0

    elif type(intercept) is shapely.geometry.multipoint.MultiPoint:
        a = intercept[0].x, intercept[0].y
        b = intercept[1].x, intercept[1].y
        distance_toll = sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    elif n_out[0] > 35 and n_out[1] > 35 and n_in[0] > 35 and n_in[1] > 35:
        tau = 1
        return tau

    else:
        tau = 0
        return tau

    distance = sqrt((n_out[0] - n_in[0]) ** 2 + (n_out[1] - n_in[1]) ** 2)
    tau = distance_toll / distance
    return tau

def distance_toll_access(n_out, n_in):
    ra = LineString([(35, 70), (35, 35), (70, 35)])
    line1 = LineString([n_out, n_in])
    intercept = line1.intersection(ra)

    if type(intercept) is shapely.geometry.point.Point:
        a = intercept.x, intercept.y
        if (n_out[0] <= 35 or n_out[1] <= 35) and (n_in[0] > 35 and n_in[1] > 35):
            tau = 1
        else:
            tau = 0

    elif type(intercept) is shapely.geometry.multipoint.MultiPoint:
        a = intercept[0].x, intercept[0].y
        b = intercept[1].x, intercept[1].y
        tau = 1

    else:
        tau = 0
        return tau
    return tau