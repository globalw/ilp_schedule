"""This script sets up a dict for the loading systems available.

   loadingsystems   -   dict((i):[w]) (w = max lifting weight)
   flighttime       -   nxn matrix ((o,d) entry gives the flight time from o to d)
"""
import numpy as np

def construct_airfraight_loadindsystems(n):
    # genereate fleet
    loadingsystems = dict()
    for i in range(n):
        if i == 0:
            w = 250
            loadingsystems[i] = w
        if i == 1:
            w = 200
            loadingsystems[i] = w
        if i == 2:
            w = 170
            loadingsystems[i] = w
        if (i < int(n*0.25) and i > 2):
            w = 140
            loadingsystems[i] = w
        if (i < int(n*0.5) and i > 5):
            w = 110
            loadingsystems[i] = w
        if (i < int(n*0.75) and i > 9):
            w = 80
            loadingsystems[i] = w
        if  i >= int(n*0.75):
            w = 50
            loadingsystems[i] = w

    return loadingsystems

def construct_matrix_flighttime(n):
    # this is the actual flight time of the aircrafts
    flighttime = np.empty((n+1, n+1))
    for i in range(n+1):
        for j in range(i+1, n+1):
                flighttime[i, j] = np.random.randint(low=1, high=2, size=1)[0]
                flighttime[j, i] = flighttime[i, j]
    return flighttime

def construct_airfraight_timeinterval(L_task):
    max = 0
    for k,v in L_task.items():
        if v[0] > max:
            max = v[0]
    T = np.arange(0, max+1, 1)
    return T

def construct_airfraight_cities(L):
    # genereate list of cities based on L
    C = [0]
    for k, v in L.items():
        if k[0] not in C:
            C.append(k[0])
        if k[1] not in C:
            C.append(k[1])
    return C

def construct_airfraight_cities(L_tasks, num_cities, flighttime):
    # genereate list of cities based on L
    C = [0]
    layer = 0
    while L_tasks[layer]:
        for k, v in L_tasks[layer].items():
            # test if cities are already in list, if not append
            if k[0] + num_cities*(layer) not in C:
                C.append(k[0] + num_cities*(layer))
            if k[1] + num_cities*(layer) not in C:
                C.append(k[1] + num_cities*(layer))
            # append flight time to L_tasks_mod extracted from flighttime matrix
            v.append(flighttime[k[0],k[1]])

        layer += 1

    # generate list of cities for the first layer
    C_first_layer = []
    for k, v in L_tasks[0].items():
        if k[0] not in C_first_layer:
            C_first_layer.append(k[0])
        if k[1] not in C_first_layer:
            C_first_layer.append(k[1])
    C_first_layer = list(np.sort(C_first_layer))

    # generate fictive layer and append it to C
    C_ficitve = []
    for k in range(len(C_first_layer)):
        C.append(C_first_layer[k] + num_cities * (layer))
        C_ficitve.append(C_first_layer[k] + num_cities * (layer))

    C_task = [0] + C_first_layer

    return list(np.sort(C)), C_task, C_ficitve

def construct_airfraight_flighttime(C, C_task, C_fictive, flighttime, L_tasks):
    # this is constructing a matrix flighttime_case. It includes all the "flighttimes"?! for all the fictive and
    # task cities
    flighttime_case = np.empty((len(C), len(C)))
    C_task_mod = C_task[1:]
    for i in C_task_mod:
        flighttime_case[i, i + len(C_task_mod)] = 0
        flighttime_case[i + len(C_task_mod), i] = 0
    for i in C_task_mod:
        for j in C_task_mod:
            if (i, j) in L_tasks:
                flighttime_case[i, j] = L_tasks[i, j][2]
    for i in C_fictive:
        for j in C_fictive:
            if i != j:
                if (i - len(C_fictive), j-len(C_fictive)) in L_tasks:
                    flighttime_case[i, j] = L_tasks[i - len(C_fictive), j - len(C_fictive)][2]
                else:
                    flighttime_case[i, j] = flighttime[i - len(C_task_mod), j - len(C_task_mod)]
    for j in C_fictive:
        flighttime_case[0, j] = flighttime[0, j - len(C_task_mod)]
        flighttime_case[j, 0] = flighttime[j - len(C_task_mod), 0]
    return flighttime_case

def construct_airfraight_transp_loadingsystems(L):
    # # this is the construction of the transportation time of the loading system...
    # # this does not have anything to do with the flight time. in fact the flighttime matrix
    # # needs to be imported from the airfraight scheduling module. But here the transportation time
    # # for the loading system seems to be defined as to be 10 time longer than the flight
    transp_time_l = dict()
    # C_task_mod = C_task[1:]
    # nb_loops = int((len(C[1:])/len(C_task_mod)) - 1)
    # for o in C_task_mod:
    #     for d in C_task_mod:
    #         if o != d:
    #             # here C_fictive actually adresses the full city list... we use this method by inputing the full
    #             # city list for C_fictive
    #             transp_time_l[o, d] = 1 * flighttime_case[C_fictive[o-1], C_fictive[d-1]]
    # # this is attempting to represent that the loading systems dont need time to get to a certain city.. or that they
    # # are there without loss of time
    # for o in C_task_mod:
    #     for i in range(1, nb_loops+1):
    #         transp_time_l[o, o + (len(C_task_mod) * i)] = 0
    #         transp_time_l[o + (len(C_task_mod) * i), o] = 0
    # L is the combination of task and fictive
    for k, v in L.items():
        transp_time_l[k] = v[2]*2

    return transp_time_l

def construct_loadingsystem_costs(transp_time_l, loadingsystems, T):
    # genereate dictionary for cost of each flight for each aircraft
    cost = dict()
    for l in loadingsystems:
        for t in T:
            for k, v in transp_time_l.items():
                cost[l, k[0], k[1], t] = loadingsystems[l] * v * 0.25
    return cost