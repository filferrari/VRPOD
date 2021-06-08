import numpy as np
import pandas as pd
import math
import gurobipy as gp
from gurobipy import GRB
from Utilities import Instance, create_tour, create_routes





# calculate distance
def capacity(d, instance: Instance):
    cap = 0
    for h in range(len(d) - 1):
        if d[h]>instance.C and len(d)>4:
            return instance.Q+1
        elif d[h]<=instance.C:
            cap += instance.q[d[h]]
        else:
            return 0
    return cap


def dist(d, instance: Instance):
    x=1
    if max(d) > instance.C:
       x=2
    if max(d) > instance.C and len(d)==3:
        return 0
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==1:
        dis = 0
        for h in range(len(d) - x):
            dis += instance.d[d[h], d[h + 1]]+instance.d[d[h], d[h + 1]]*instance.T*instance.t[d[h], d[h + 1]]
        dis-=instance.d[d[0], d[d.index(max(d))]] + instance.d[d[0], d[d.index(max(d))]] * instance.T * instance.t[d[0], d[d.index(max(d))]]

        return dis*instance.rho
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==0:
        dis = 0
        for h in range(len(d) - x):
            dis += instance.d_sd[d[h], d[h + 1]]
        dis-=instance.d_sd[d[0], d[d.index(max(d))]]

        return dis*instance.rho
    dis = 0
    for h in range(len(d) - x):
        dis += instance.d[d[h], d[h + 1]]+instance.d[d[h], d[h + 1]]*instance.T*instance.t[d[h], d[h + 1]]
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
            dis += instance.d[d[h], d[h + 1]]*instance.T*instance.t[d[h], d[h + 1]]
        dis-=instance.d[d[0], d[d.index(max(d))]] * instance.T * instance.t[d[0], d[d.index(max(d))]]

        return dis
    if max(d) > instance.C and len(d) == 4 and instance.v[max(d)-instance.C-1]==0:
        return 0
    dis = 0
    for h in range(len(d) - x):
        dis += instance.d[d[h], d[h + 1]]*instance.T*instance.t[d[h], d[h + 1]]
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

    #print("Applying 2-opt(steepest descent) to", start, "...")
    x = 1
    mindist = dist(start, instance = instance)
    currentbest = start[:]
    count = 1

    while (count >= 1):
        count = 0
        for i in range(1, len(start) - 2):
            for j in range(1 + i, len(start) - 1):
                if dist(swap(start, i, j), instance = instance) < mindist:
                    mindist = dist(swap(start, i, j), instance = instance)
                    currentbest = swap(start, i, j)[:]
                    count += 1
        start = currentbest[:]

    #print("... The solution is:", start, " with a distance of", mindist)
    return start

def tourswap(j,k,x,y):
    dj = j[:]
    dk = k[:]
    dj.insert(j.index(x),y)
    #dj.insert(k.index(y), x)
    #dj.remove(x)
    dk.remove(y)
    return [dj,dk]



def heuristic_dist(instance: Instance):

    customers = instance.C+instance.K
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
                 x[v] = twoopt(x[v], instance = instance)
            #print(dist(x[v],instance = instance))
            leng += dist(x[v], instance = instance)
    print("The final tours are: ", x, "with a total length of: ", leng)
    sol = []
    for i in x:
        #if max(x[i])> instance.C:
            #x[i].pop(len(x[i])-1)
        sol.append(x[i])

    cost = 0
    for v in range(len(sol)):
        cost += dist(sol[v], instance=instance)
    savingstoll = 0
    for v in range(len(sol)):
        savingstoll += toll(sol[v], instance=instance)
    nrod = 0
    for v in range(len(sol)):
        if max(sol[v]) > instance.C and len(sol[v]) == 4:
            nrod += 1
    odcomp = 0
    for v in range(len(sol)):
        if max(sol[v]) > instance.C and len(sol[v]) == 4:
            odcomp += dist(sol[v], instance=instance)
    print("Final tours Savings", sol)
    print("Final cost Savings", cost)
    print("Final ODs used Savings", nrod)
    print("Final OD compensation Savings", odcomp)
    print("Final toll Savings", savingstoll)

    for i in range(len(sol)):
        if max(sol[i]) > instance.C:
            sol[i].pop(len(sol[i]) - 1)


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
                                    
    """


    return sol













