import numpy as np
import pandas as pd
import math
import gurobipy as gp
from gurobipy import GRB
from Utilities import Instance, create_tour, create_routes


# tsp reformulated to accept specific routes to optimize
def tsp(cities, instance: Instance):
    #print("these are cities", cities)
    cities1zero = []
    for i in range(1, len(cities)):
        cities1zero.append(cities[i])
    cities0zero = []
    for i in range(1, len(cities) - 1):
        cities0zero.append(cities[i])
    m = gp.Model("Travelling Salesman Problem")

    # Create variables
    travel = {}
    z = {}
    for i in cities1zero:
        z[i] = m.addVar()
        for j in cities1zero:
            travel[i, j] = m.addVar(vtype=GRB.BINARY, obj=instance.d[i, j])

    # departure constraints
    for i in cities1zero:
        m.addConstr(sum(travel[i, j] for j in cities1zero) == 1)

    # arrival constraints
    for j in cities1zero:
        m.addConstr(sum(travel[i, j] for i in cities1zero) == 1)

    # Subtourelimination

    for i in cities0zero:
        for j in cities0zero:
            if i != j:
                m.addConstr(z[i] - z[j] + len(cities0zero) * travel[i, j] <= len(cities0zero) - 1)

    # m.Params.TimeLimit=600
    # m.Params.MIPGap=0.1
    m.optimize()

    print(m.objVal)

    for i in cities1zero:
        for j in cities1zero:
            print(travel[i, j].x, i, j, "i,j")

    tour = [0]
    y = 0
    #print("cities", len(cities))
    while len(tour) < len(cities):
        for i in cities:
            for j in cities:
                if travel[i, j].x > m.params.IntFeasTol and i == tour[y] and len(tour) < len(cities):
                    tour.append(j)
                    y += 1

    # global total
    # total += dist(result)

    m.dispose()

    return tour


# calculate distance
def capacity(d, instance: Instance):
    cap = 0
    for h in range(1, len(d) - 1):
        if d[h] > instance.C and len(d) > 4:
            return instance.Q + 1
        elif d[h] <= instance.C:
            cap += instance.nodes[d[h]]["demand"]
            # instance.q[d[h]]
        else:
            return 0
    return cap

"""
def dist(d, instance: Instance):
    if any(y > instance.C for y in d) and len(d) == 3:
        return 0
    if any(y > instance.C for y in d) and len(d) == 4:
        dis = 0
        for h in range(len(d) - 2):
            dis += instance.d_sd[d[h], d[h + 1]]
        dis -= instance.d_sd[d[0], d[d.index(max(d))]]
        return dis * instance.rho
    dis = 0
    for h in range(len(d) - 1):
        dis += instance.d_sd[d[h], d[h + 1]]
    return dis
"""

def dist(d, instance: Instance):
    x=1
    if max(d) > instance.C:
       x=2
    if max(d) > instance.C and len(d)==3:
        return 0
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==1:
        dis = 0
        for h in range(len(d) - x):
            dis += instance.d[d[h], d[h + 1]]+instance.T*instance.t[d[h], d[h + 1]]
        dis-=instance.d[d[0], d[d.index(max(d))]]+instance.T*instance.t[d[0], d[d.index(max(d))]]
        return dis*instance.rho
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==0:
        dis = 0
        for h in range(len(d) - x):
            dis += instance.d_sd[d[h], d[h + 1]]
        dis-=instance.d_sd[d[0], d[d.index(max(d))]]
        return dis*instance.rho
    dis = 0
    for h in range(len(d) - x):
        dis += instance.d[d[h], d[h + 1]]+instance.T*instance.t[d[h], d[h + 1]]
    return dis


def toll(d, instance: Instance):
    x=1
    if max(d) > instance.C:
       x=2
    if max(d) > instance.C and len(d)==3:
        return 0
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==1:
        dis = 0
        for h in range(len(d) - x):
            dis += instance.T*instance.t[d[h], d[h + 1]]
        dis-=instance.T*instance.t[d[0], d[d.index(max(d))]]
        return dis
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==0:
        return 0
    dis = 0
    for h in range(len(d) - x):
        dis += instance.T*instance.t[d[h], d[h + 1]]
    return dis

def realdistOD(d, instance: Instance):

    if any(y > instance.C for y in d) and len(d) == 4:
        dis = 0
        for h in range(len(d) - 2):
            dis += instance.d_sd[d[h], d[h + 1]]
        return dis

def newtour(a, b):
    tour = []
    tour.append(0)
    for x in range(1, len(a) - 1):
        tour.append(a[x])
    for y in range(1, len(b) - 1):
        tour.append(b[y])
    tour.append(0)
    return tour


def swap(d, i, j):
    di = d[:]
    di[i] = d[j]
    di[j] = d[i]
    if ((j - i) >= 3):
        for k in range(int((j - i - 1) / 2)):
            di[i + k + 1] = d[j - k - 1]
            di[j - k - 1] = d[i + k + 1]
    return di


def twoopt(start, instance: Instance):
    # print("Applying 2-opt(steepest descent) to", start, "...")
    x = 1
    mindist = dist(start, instance=instance)
    currentbest = start[:]
    count = 1

    while (count >= 1):
        count = 0
        for i in range(1, len(start) - 2):
            for j in range(1 + i, len(start) - 1):
                if dist(swap(start, i, j), instance=instance) < mindist:
                    mindist = dist(swap(start, i, j), instance=instance)
                    currentbest = swap(start, i, j)[:]
                    count += 1
        start = currentbest[:]

    # print("... The solution is:", start, " with a distance of", mindist)
    return start


def tourswap(j, k, x, y):
    dj = j[:]
    dk = k[:]
    dj.insert(j.index(x), y)
    # dj.insert(k.index(y), x)
    # dj.remove(x)
    dk.remove(y)
    return [dj, dk]


def heuristic_sweep_access(instance: Instance):
    customers = instance.C + instance.K
    maxsaving = 1
    saveroute = {}
    x = {}
    for j in range(customers):
        x[j] = [0, j + 1, 0]

    #print(x)
    while maxsaving > 0:
        maxsaving = 0
        parent1 = customers + 1
        parent2 = customers + 1
        for k in range(customers):
            for l in range(k, customers):
                if k != l and k in x and l in x and (l <= instance.C - 1 or k <= instance.C - 1):
                    if (dist(x[k], instance=instance) + dist(x[l], instance=instance) - dist(newtour(x[k], x[l]),
                                                                                             instance=instance)) > maxsaving and (
                    capacity(newtour(x[k], x[l]), instance=instance)) <= instance.Q and (
                            l <= instance.C - 1 and k <= instance.C - 1):

                        maxsaving = dist(x[l], instance=instance) + dist(x[k], instance=instance) - dist(
                            newtour(x[k], x[l]), instance=instance)
                        saveroute = newtour(x[k], x[l])
                        parent1 = k
                        parent2 = l
                    elif (dist(x[k], instance=instance) + dist(x[l], instance=instance) - dist(newtour(x[k], x[l]),
                                                                                               instance=instance)) > maxsaving and (
                    capacity(newtour(x[k], x[l]), instance=instance)) <= instance.Q and l > instance.C - 1 and len(
                            newtour(x[k], x[l])) == 4 and (
                            realdistOD(newtour(x[k], x[l]), instance=instance) - instance.d_sd[
                        0, l + 1]) < instance.max_dev * instance.d_sd[0, l + 1]:

                        maxsaving = dist(x[l], instance=instance) + dist(x[k], instance=instance) - dist(
                            newtour(x[k], x[l]), instance=instance)
                        saveroute = newtour(x[k], x[l])
                        parent1 = k
                        parent2 = l
                    elif (dist(x[k], instance=instance) + dist(x[l], instance=instance) - dist(newtour(x[k], x[l]),
                                                                                               instance=instance)) > maxsaving and (
                    capacity(newtour(x[k], x[l]), instance=instance)) <= instance.Q and k > instance.C - 1 and len(
                            newtour(x[k], x[l])) == 4 and (
                            realdistOD(newtour(x[k], x[l]), instance=instance) - instance.d_sd[
                        0, k + 1]) < instance.max_dev * instance.d_sd[0, k + 1]:
                        maxsaving = dist(x[l], instance=instance) + dist(x[k], instance=instance) - dist(
                            newtour(x[k], x[l]), instance=instance)
                        saveroute = newtour(x[k], x[l])
                        parent1 = k
                        parent2 = l
        if parent1 != customers + 1:
            del x[parent1]
            del x[parent2]
            x[parent1] = saveroute
        """print(maxsaving)
        print(saveroute)
        print(x)"""

    leng = 0
    for v in range(customers):
        if v in x:
            if max(x[v]) <= instance.C:
                x[v] = twoopt(x[v], instance=instance)
            #print(dist(x[v], instance=instance))
            leng += dist(x[v], instance=instance)
    print("The final tours are: ", x, "with a total length of: ", leng)
    sol = []
    for i in x:
        # if max(x[i])> instance.C:
        sol.append(x[i])

    #print("before", sol)
    cost = 0
    for v in range(len(sol)):
        cost += dist(sol[v], instance=instance)
    #print(cost)
    """
    odtourss=[]
    for x in range(instance.K):
        best=np.inf
        bestcust=np.inf
        for y in range(1,instance.C+1):
            if instance.d_sd[y,instance.C+1+x]<best:
                best=instance.d_sd[y,instance.C+1+x]
                bestcust=y
        odtourss.append([0,bestcust,instance.C+1+x,0])
    """

    """
    for j in range(len(sol)):
            for k in range(j,len(sol)):
                if j != k and max(sol[j])<=instance.C and max(sol[k])<=instance.C:
                    for x in sol[j]:
                        for y in sol[k]:
                            if x !=0 and y!= 0:
                                #print(sol[k],sol[j])
                                sw=tourswap(sol[j],sol[k],x,y)
                                sw[0]=twoopt(sw[0],instance=instance)
                                sw[1] = twoopt(sw[1], instance=instance)
                                #print(sw)
                                if (dist(sol[j], instance = instance)+dist(sol[k], instance = instance))>(dist(sw[0], instance = instance)+dist(sw[1], instance = instance))and(capacity(sw[0],instance=instance)<= instance.Q) and (capacity(sw[1],instance=instance) <= instance.Q):
                                    print("better")
                                    sol[j]=sw[0][:]
                                    sol[k]=sw[1][:]
    for j in range(len(sol)):
            for k in range(j, len(sol)):
                if j != k and max(sol[j]) <= instance.C and max(sol[k]) <= instance.C:
                    for x in sol[j]:
                        for y in sol[k]:
                            if x != 0 and y != 0:
                                # print(sol[k],sol[j])
                                sw = tourswap(sol[k], sol[j], y, x)
                                sw[0] = twoopt(sw[0], instance=instance)
                                sw[1] = twoopt(sw[1], instance=instance)
                                # print(sw)
                                if (dist(sol[j], instance=instance) + dist(sol[k], instance=instance)) > (dist(sw[0], instance=instance) + dist(sw[1], instance=instance)) and (capacity(sw[0],instance=instance)<=instance.Q) and (capacity(sw[1],instance=instance)<=instance.Q):
                                    print("better")
                                    sol[j] = sw[0][:]
                                    sol[k] = sw[1][:]

    for v in range(len(sol)):
        if max(sol[v]) <= instance.C:
            sol[v]=tsp(sol[v], instance=instance)[:]
            print("tset", sol[v])
    """
    RDtour = [0]
    for v in range(len(sol)):
        if max(sol[v]) <= instance.C:
            sol[v].pop(0)
            sol[v].pop(len(sol[v]) - 1)
            for x in range(len(sol[v])):
                RDtour.append(sol[v][x])
    RDtour.append(0)
    """
    RDtour = [0]
    for i in range(1,instance.C+1):
        if not any(i in sublist for sublist in odtourss):

            RDtour.append(i)
    RDtour.append(0)
    """

    y = {}
    co = []
    for x in range(len(RDtour) - 1):
        for f in instance.nodes:
            if f["id"] == RDtour[x]:
                co.append([f["x"], f["y"]])
        #print("co", co)

    #print("RDtour", RDtour)
    customers = len(RDtour) - 2
    #print("customers", customers)
    #print("co", len(co))

    polar = [[0 for col in range(3)] for row in range(customers + 1)]
    ci = [[0 for col in range(2)] for row in range(customers + 1)]

    for i in range(1, customers + 1):
        co[i][0] = co[i][0] - 35
        co[i][1] = co[i][1] - 35
        polar[i][0] = co[i][0]
        polar[i][1] = co[i][1]

        if co[i][0] > 0 and co[i][1] > 0:
            polar[i][2] = math.degrees(math.atan(co[i][1] / co[i][0]))
        if co[i][0] > 0 and co[i][1] == 0:
            polar[i][2] = 0
        if co[i][0] < 0 and co[i][1] > 0:
            polar[i][2] = 180 + math.degrees(math.atan(co[i][1] / co[i][0]))
        if co[i][0] == 0 and co[i][1] > 0:
            polar[i][2] = 90
        if co[i][0] < 0 and co[i][1] < 0:
            polar[i][2] = 180 + math.degrees(math.atan(co[i][1] / co[i][0]))
        if co[i][0] < 0 and co[i][1] == 0:
            polar[i][2] = 180
        if co[i][0] > 0 and co[i][1] < 0:
            polar[i][2] = 360 + math.degrees(math.atan(co[i][1] / co[i][0]))
        if co[i][0] == 0 and co[i][1] < 0:
            polar[i][2] = 270

    polar.sort(key=lambda x: x[2])

    #print("polar", polar)
    mintour = []
    mincost = np.inf

    for i in range(1, customers + 1):
        co[i][0] = co[i][0] + 35
        co[i][1] = co[i][1] + 35
        ci[i][0] = polar[i][0] + 35
        ci[i][1] = polar[i][1] + 35
    mintour = []
    mincost = np.inf
    for i in range(len(RDtour)):
        if i != 0:
            #print("§§§§§§§§§§§§§§§§§§§", ci)
            ci.append(ci[1])
            ci.pop(1)
            #print("§§§§§§§§§§§§§§§§§§§", ci)
        """
        # compute distance matrix

        distance = np.zeros((customers + 1, customers + 1))

        for i in range(customers + 1):
            for j in range(customers + 1):
                if (i == j):
                    distance[i, j] = 10000
                else:
                    distance[i, j] = math.sqrt(
                        (ci[i][0] - ci[j][0]) * (ci[i][0] - ci[j][0]) + (ci[i][1] - ci[j][1]) * (ci[i][1] - ci[j][1]))


        def distsweep(d):
            dis = 0
            for h in range(len(d) - 1):
                dis += distance[d[h]][d[h + 1]]
            return dis
        """

        def add(a, b):
            tour = []
            tour.append(0)
            for x in range(1, len(a) - 1):
                tour.append(a[x])
            tour.append(b)
            tour.append(0)
            return tour

        """print("$$$$$$$$$$$$$$$$$", RDtour[co.index(ci[1])])
        print("$$$$$$$$$$$$$$$$$", RDtour[co.index(ci[2])])
        print("$$$$$$$$$$$$$$$$$", RDtour[co.index(ci[3])])
        print("$$$$$$$$$$$$$$$$$", RDtour[co.index(ci[4])])
        print("$$$$$$$$$$$$$$$$$", RDtour[co.index(ci[5])])

        print(ci[1])
        print(co.index(ci[1]))
        print(instance.nodes)
        print(RDtour)
        print(ci)
        print(co)"""

        j = 0
        y[0] = [0, RDtour[co.index(ci[1])], 0]
        for i in range(customers - 1):
            #print(i, j, "i,j")
            if capacity(add(y[j], RDtour[co.index(ci[i + 2])]), instance=instance) <= instance.Q:
                y[j] = add(y[j], RDtour[co.index(ci[i + 2])])
            else:
                j += 1
                y[j] = [0, RDtour[co.index(ci[i + 2])], 0]

        # Travelling salesman
        final = []
        for i in range(customers):

            # determine optimal solution

            if i in y:
                #print(y[i])
                # final.append(tsp(y[i],instance=instance))
                final.append(twoopt(y[i], instance=instance))
                # final.append(y[i])

        cost = 0
        for v in range(len(final)):
            cost += dist(final[v], instance=instance)
        #print(cost)
        #print("Final routes: ", final, "Toutal cost: ", cost)

        for v in range(len(sol)):
            if max(sol[v]) > instance.C:
                final.append(sol[v])

        # for v in range(len(odtourss)):
        #    if max(odtourss[v]) > instance.C:
        #         final.append(odtourss[v])

        cost = 0
        for v in range(len(final)):
            cost += dist(final[v], instance=instance)
        #print(cost)
        #print("Final routes: ", final, "Toutal cost: ", cost)
        if cost < mincost:
            mincost = cost
            mintour = final[:]
    sol = mintour[:]

    cost = 0
    for v in range(len(sol)):
        cost += dist(sol[v], instance=instance)
    sweeptoll = 0
    for v in range(len(sol)):
        sweeptoll += toll(sol[v], instance=instance)
    nrod = 0
    for v in range(len(sol)):
        if max(sol[v]) > instance.C and len(sol[v]) == 4:
            nrod += 1
    odcomp = 0
    for v in range(len(sol)):
        if max(sol[v]) > instance.C and len(sol[v]) == 4:
            odcomp += dist(sol[v], instance=instance)
    print("Final tours Sweep", sol)
    print("Final cost Sweep", cost)
    print("Final ODs used Sweep", nrod)
    print("Final OD compensation Sweep", odcomp)
    print("Final toll Sweep", sweeptoll)

    for v in range(len(sol)):
        if max(sol[v]) > instance.C:
            sol[v].pop(len(sol[v]) - 1)

    return sol













