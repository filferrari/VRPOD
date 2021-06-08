import pandas as pd
from random import randrange


def read(filename):
    nodes = list()
    coordinates = pd.read_excel(filename, sheet_name="Coordinates")
    co = coordinates.values.tolist()
    demand = pd.read_excel(filename, sheet_name="Demand", usecols=[0])
    de = demand.values.flatten().tolist()

    # Customers
    c = len(co)-1

    # Nodes
    for i in range(len(co)):
        x = co[i][0]
        y = co[i][1]
        demand = de[i]
        nodes.append({"id": i, "x": x, "y": y, "demand": demand})

    return {'c': c, 'nodes': nodes}


def od_destinations(number, filename):
    locations = list()
    coordinates = pd.read_excel(filename, sheet_name="Coordinates")
    co = coordinates.values.tolist()
    c = len(co) - 1

    x_co = pd.read_excel(filename, sheet_name="Coordinates", index_col=1)
    co_x = x_co.values.flatten().tolist()
    y_co = pd.read_excel(filename, sheet_name="Coordinates", index_col=0)
    co_y = y_co.values.flatten().tolist()

    min_x = min(co_x)
    max_x = max(co_x)
    min_y = min(co_y)
    max_y = max(co_y)

    for k in range(number):
        x = randrange(min_x, max_x)
        y = randrange(min_y, max_y)
        id = c+k+1
        locations.append({"id": id, "x": x, "y": y})
    return locations

#print(read("solomon 50.xlsx"))
#print(od_destinations(5,"solomon 50.xlsx"))




