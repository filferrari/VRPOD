# Vehicle Routing Problem with Occasional Drivers (VRPOD) by Archetti et al. (2016)
# set of nodes = RDs + C + ODs
# (single) depot location = {0}
# set of customer locations c = {1, ... ,C}
# set of OD destinations K = {OD_1, ..., OD_K}
# each customers has a certain demand q_i
# that has to be fulfilled by exactly one vehicle (no split deliveries), which can be an RD or an OD
# each RD vehicles has a maximum load capacity of Q that cannot be exceeded
# RDs start from and end their tour in the depot l_0
# ODs start from l_o and end at the respective destination
# and are only allowed to make a (single) delivery if the detour length is not too big
# Goal: minimize total delivery cost (RDs delivery cost + ODs compensation)

from Utilities import Instance, create_tour, create_routes
import gurobipy as gp
from gurobipy import *


def solve_VRPOD (instance: Instance):
    m = gp.Model("VRPOD_Archetti")

    ### DECISION VARIABLES
    # x_ij: indicates whether an RD transverses arc(i,j)
    # y_ij: represents the load carried by an RD on the arc(i,j)
    # w_ik: indicates whether customer i is served by OD k
    # z_i:  indicates whether customer i is served by an RD
    x = dict()
    for node_i, node_j in instance.dRD.keys():
        x[node_i, node_j] = m.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=f'RD sub-tour{node_i, node_j}')
    m.update()
    y = dict()
    for node_i, node_j in instance.dRD.keys():
        y[node_i, node_j] = m.addVar(lb=0.0, vtype=gp.GRB.CONTINUOUS, name=f'Load{node_i, node_j}')
    m.update()
    w = dict()
    for i in range(1, instance.C +1):
        for k in range(1, instance.K +1):
            OD = instance.C + k
            w[i, OD] = m.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=f'OD match{i, OD}')
    m.update()
    z = dict()
    for i in range(1, instance.C +1):
        z[i] = m.addVar(lb=0.0, ub=1.0, vtype=gp.GRB.BINARY, name=f'RD match{i}')
    m.update()

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
    m.update()

    ###OBJECTIVE FUNCTION
    # (1) OBJ = (RD costs + OD compensation)
    RD_costs = LinExpr()
    for node_i, node_j in instance.dRD.keys():
        RD_costs += x[node_i, node_j] * instance.d[node_i, node_j] * instance.CF

    OD_compensation = LinExpr()
    for i in range(1, instance.C +1):
        for k in range(1, instance.K +1):
            OD = instance.C + k
            OD_compensation += p[i, OD] * w[i, OD]

    obj = RD_costs + OD_compensation
    m.setObjective(obj, sense=gp.GRB.MINIMIZE)
    m.update()

    ###CONSTRAINTS
    # (2) flow conservation
    for i in range(1, instance.C +1):
        x_ij = LinExpr()
        x_ji = LinExpr()
        for n in instance.nodesRD:
            x_ij += x[i, n["id"]]
            x_ji += x[n["id"], i]
        m.addConstr(lhs=x_ij, sense=gp.GRB.EQUAL, rhs=z[i])
        m.addConstr(lhs=x_ji, sense=gp.GRB.EQUAL, rhs=z[i])
    m.update()

    # (3) flow conservation
    x_0j = LinExpr()
    x_j0 = LinExpr()
    for n in instance.nodesRD:
        x_0j += x[0, n["id"]]
        x_j0 += x[n["id"], 0]
    sub = x_0j - x_j0
    m.addConstr(lhs=sub, sense=gp.GRB.EQUAL, rhs=0)
    m.update()

    # (4) demand fulfillment and prevention of sub-tours (RD)
    load_carried = LinExpr()
    for i in range(1, instance.C +1):
        y_ij = LinExpr()
        y_ji = LinExpr()
        demand_i = instance.q[i] * z[i]
        load_carried += demand_i
        for n in instance.nodesRD:
            y_ij += y[i, n["id"]]
            y_ji += y[n["id"], i]
        sub = y_ji - y_ij
        m.addConstr(lhs=sub, sense=gp.GRB.EQUAL, rhs=demand_i)

    y_ij = LinExpr()
    y_ji = LinExpr()
    load_carried = load_carried * (-1)
    for n in instance.nodesRD:
        y_ij += y[0, n["id"]]
        y_ji += y[n["id"], 0]
    sub = y_ji - y_ij
    m.addConstr(lhs=sub, sense=gp.GRB.EQUAL, rhs=load_carried)
    m.update()

    # (5) RD vehicle capacity
    for node_i, node_j in instance.dRD.keys():
        load_ij = y[node_i, node_j]
        rd_capacity = instance.Q * x[node_i, node_j]
        m.addConstr(lhs=load_ij, sense=gp.GRB.LESS_EQUAL, rhs=rd_capacity)
    m.update()

    # (6) RD vehicle returns empty to the depot
    for i in range(1, instance.C +1):
        final_load = y[i, 0]
        m.addConstr(lhs=final_load, sense=gp.GRB.EQUAL, rhs=0)
    m.update()

    # (7) customer is assigned to an OD willing/allowed to serve him
    for i in range(1, instance.C +1):
        for k in range(1, instance.K +1):
            OD = instance.C + k
            m.addConstr(lhs=w[i, OD], sense=gp.GRB.LESS_EQUAL, rhs=beta[i, OD])
    m.update()

    # (8) OD single delivery
    for k in range(1, instance.K +1):
        od_deliveries = LinExpr()
        for i in range(1, instance.C +1):
            OD = instance.C + k
            od_deliveries += w[i, OD]
        m.addConstr(lhs=od_deliveries, sense=gp.GRB.LESS_EQUAL, rhs=1)
    m.update()

    # (9) each customer is served once
    for i in range(1, instance.C +1):
        delivery = LinExpr()
        for k in range(1, instance.K +1):
            OD = instance.C + k
            delivery += w[i, OD]
        delivery += z[i]
        m.addConstr(lhs=delivery, sense=gp.GRB.EQUAL, rhs=1)
    m.update()

    m.optimize()

    if m.Status == gp.GRB.OPTIMAL:
        arcs_used = dict()
        distance_rd = 0
        distance_od = 0
        for node_i, node_j in x:
            arcs_used[node_i, node_j] = (x[node_i, node_j].X >= m.params.IntFeasTol)
            distance_rd += instance.d[node_i, node_j] * (x[node_i, node_j].X >= m.params.IntFeasTol)
        interim_solution_rd = create_tour(arcs_used)
        #print("arcs_used: ", arcs_used)
        #print("interim_solution_rd: ",interim_solution_rd)
        solution_rd = create_routes(interim_solution_rd)
        #print (solution)

        customers_rd = list()
        customers_od = list()
        for i in range(1, instance.C +1):
            if z[i].X >= m.params.IntFeasTol:
                customers_rd.append(i)
            for k in range(1, instance.K+1):
                OD = instance.C + k
                if w[i, OD].X >= m.params.IntFeasTol:
                    customers_od.append((i, OD))
                    distance_od += instance.d[0, i] + instance.d[i, OD]

        return solution_rd, m.ObjVal, RD_costs.getValue(), OD_compensation.getValue(), customers_rd, customers_od, distance_rd, distance_od
    
    elif m.Status == gp.GRB.INFEASIBLE:
        message_1 = 'Model is infeasible'
        return message_1
    
    else:
        message_2 = 'Model could not be solved to optimality'
        return message_2

