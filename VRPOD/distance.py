import shapely
from shapely.geometry import LineString
from math import sqrt


n_out = (41, 49) # node 1
n_in = (35, 35)  # node 0
ra = LineString([(35, 70), (35, 35), (70, 35)])
line1 = LineString([n_out, n_in])
intercept = line1.intersection(ra)
tau = 0

if type(intercept) is shapely.geometry.point.Point:
    a = intercept.x, intercept.y
    print(a)
    if (n_out[0] <= 35 or n_out[1] <= 35) and (n_in[0] > 35 and n_in[1] > 35):
        distance_toll = sqrt((a[0] - n_in[0]) ** 2 + (a[1] - n_in[1]) ** 2)
    else:
        distance_toll = 0
    print(distance_toll)

elif type(intercept) is shapely.geometry.multipoint.MultiPoint:
    a = intercept[0].x, intercept[0].y
    b = intercept[1].x, intercept[1].y
    distance_toll = sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)
    print(a)
    print(b)
else:
    tau = 0

distance = sqrt((n_out[0] - n_in[0]) ** 2 + (n_out[1] - n_in[1]) ** 2)
tau = distance_toll / distance
print("tau:", tau)
print(distance)