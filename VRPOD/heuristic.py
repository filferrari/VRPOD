from typing import List, Tuple
from Utilities import Instance
from random import *


def clarke_and_wright(instance: Instance) -> List[List[int]]:
    savings: List[Tuple[int, int, float]] = list()
    for i in range(1, instance.C +1):
        for j in range(1, instance.C +1):
            if i != j:
                s_ij = instance.d[i, 0] + instance.d[j, 0] - instance.d[i, j]
                savings.append((i, j, s_ij))

    savings.sort(key=lambda entry: entry[2], reverse=True)

    # ignore depot node during construction
    R = list()
    for i in range(1, instance.C +1):
        R.append([i])

    for (i, j, s_ij) in savings:
        r_i = None
        r_j = None
        for r in R:
            if r[-1] == i:
                r_i = r
            elif r[0] == j:
                r_j = r
        if r_i is not None and r_j is not None:
            # check capacity constraint
            capacity = 0
            for i in r_i:
                capacity += instance.q[i]
            for i in r_j:
                capacity += instance.q[i]

            if capacity <= instance.Q:
                r_i.extend(r_j)
                R.remove(r_j)
    for r in R:
        r.insert(0, 0)
        r.append(0)
    return R


def heuristic(instance: Instance, k_max):
    ###PARAMETER CALCULATION
    # p_ik:    total compensation for OD k serving customer I
    # beta_ik: indicates whether OD k can serve customer i
    p = dict()
    beta = dict()
    for i in range(1, instance.C +1):
        for k in range(1, instance.K +1):
            OD = instance.C + k
            od_original_route = instance.d[0, OD]
            od_delivery_route = instance.d[0, i] + instance.d[i, OD]
            chargeable_distance = od_delivery_route - od_original_route
            p[i, OD] = instance.rho * chargeable_distance
            if od_delivery_route <= instance.max_dev * od_original_route:
                beta[i, OD] = 1
            else:
                beta[i, OD] = 0

    # (1) Start with the max. number of ODs serving the customer i for which p[i, k] is minimal.
    OD_customers = list()
    for k in range(1, instance.K + 1):
        OD = instance.C + k
        min_compensation = 1000
        min_comp_customer = 0
        for i in range(1, instance.C + 1):
            if p[i, OD] <= min_compensation:
                min_comp_customer = i
        OD_customers.append(i)

    # (2) The initial RD tours are based on a savings heuristic
    RD_customers = instance.C - instance.K
    RD_nodes = instance.nodes.copy()
    RD_q = instance.q.copy()
    for i in RD_nodes:
        if i in OD_customers:
            del RD_nodes[i]
            RD_q.pop(i)

    RD_instance = Instance(RD_customers, instance.K, instance.Q, instance.T, instance.max_dev, instance.rho, instance.CF, instance.RD_nodes, instance.nodesRD, instance.nodesRD_WD, instance.RD_q, instance.m, instance.l, instance.v, instance.t, instance.d, instance.dRD, instance.dRD_WD)
    RD_tours = clarke_and_wright(RD_instance)

    S = ...

    # (3) Improvement --> Neighborhood Search
    k = 0
    while k != k_max:
        ...
        k += 1
    return S
