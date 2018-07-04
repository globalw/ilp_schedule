"""This script sets up fixed data based on F

    L       - dict{(o,d):[td,w,f_time]  - L_task and L_fictive
    L_task  - dict{(o,d):[td,w,f_time]  - tasks (flights)
    F       - dict{f:[w_max,t_max]      - fleet
    C       - list                      - cities (based on L)
    cost    - dict{(f,o,d,t):value}     - cost matrix (value = (w_max-w)*f_time)

"""

import numpy as np
import random
import itertools as it
import airfraight.composition.flighttimematrix as ftm

def make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities):
    L_tasks = construct_airfraight_tasks(tasksize, num_cities)
    #L_tasks = []
    #L_tasks.append({(1, 50): [10, 100, 2]})
    #L_tasks.append({(1, 50): [10, 150, 2]})
    #L_tasks.append({(1, 50): [10, 100, 1]})
    #L_tasks.append({})

    F = construct_airfraight_fleet(10)

    timestep = 0

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, T, flight_time_matrix, cost = \
        update_airfraight_initial_inst(L_tasks, F, timestep, num_cities)
    return L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost

def adjust_airfraight_inst_with_loadingtime_offset(L_tasks, F, timestep, num_cities,loadingtimeoffset, flight_time_matrix):
    # add the loadingtime offset to the flighttime
    for layer in range(len(L_tasks)):
        for k in L_tasks[layer]:
            L_tasks[layer][k][2] = L_tasks[layer][k][2] + loadingtimeoffset

    T = construct_airfraight_timeinterval(L_tasks, timestep)

    C_task, L_tasks_modified = construct_airfraight_cities(L_tasks, num_cities)
    C_fictive = construct_airfraight_cities_fictive(L_tasks, C_task, num_cities)
    C = C_task + C_fictive

    flight_time_matrix = ftm.FlightTimeMatrix()
    flight_time_matrix.construct_matrix_flighttime(num_cities)

    L_ficitve = construct_possible_flights(flight_time_matrix, C_fictive, C_task, L_tasks, num_cities)
    L = {**L_tasks_modified, **L_ficitve}
    cost = construct_airfraight_costs(L, F, T)

    return L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost



def update_airfraight_inst(L_tasks, F, timestep, num_cities, flight_time_matrix):

    T = construct_airfraight_timeinterval(L_tasks, timestep)

    C_task, L_tasks_modified = construct_airfraight_cities(L_tasks, num_cities)
    C_fictive = construct_airfraight_cities_fictive(L_tasks, C_task, num_cities)
    C = C_task + C_fictive

    L_ficitve = construct_possible_flights(flight_time_matrix, C_fictive, C_task, L_tasks, num_cities)
    L = {**L_tasks_modified, **L_ficitve}
    # combine to L
    # L = combine_to_L(L_tasks_modified, L_ficitve)
    cost = construct_airfraight_costs(L, F, T)

    return L, L_tasks, L_tasks_modified, C, C_task, C_fictive, T, flight_time_matrix, cost

def update_airfraight_initial_inst(L_tasks, F, timestep, num_cities):

    T = construct_airfraight_timeinterval(L_tasks, timestep)

    C_task, L_tasks_modified = construct_airfraight_cities(L_tasks, num_cities)
    C_fictive = construct_airfraight_cities_fictive(L_tasks, C_task, num_cities)
    C = C_task + C_fictive

    flight_time_matrix = ftm.FlightTimeMatrix()
    flight_time_matrix.construct_matrix_flighttime(num_cities)

    L_ficitve = construct_possible_flights(flight_time_matrix, C_fictive, C_task, L_tasks, num_cities)
    L = {**L_tasks_modified, **L_ficitve}
    # combine to L
    # L = combine_to_L(L_tasks_modified, L_ficitve)
    cost = construct_airfraight_costs(L, F, T)
    return L, L_tasks, L_tasks_modified, C, C_task, C_fictive, T, flight_time_matrix, cost

def construct_airfraight_tasks(tasksize, num_cities):
    # TODO exclude 0 from the tasks... we defined it that way...Done?
    layer = 0
    maxlayer = 20  # the nuber of flights we allow for on edge

    # we need to define a maximum layer size for the ovelaps ->
    # L list of tasks with one flight

    L_tasks = [dict() for i in range(maxlayer)]
    # randomly generate tasks with o != d . If start and destin-
    # nation overlap stack them in a second dictionary and
    # combine them in a list
    rs = list(np.random.randint(low=1, high=num_cities+1, size=tasksize))
    #rs = random.sample(range(1, tasksize+1), tasksize)
    os = random.sample(rs + rs, int(np.sqrt(tasksize)))
    ds = random.sample(rs + rs, int(np.sqrt(tasksize)))

    # all the flight times
    all_task_details = []

    for (o, d) in it.product(os, ds):

        deadlinetime = np.random.randint(low=10+tasksize, high=tasksize*10+tasksize+1, size=1)[0]
        weight = np.random.randint(low=2, high=200, size=1)[0]
        f_time = np.random.randint(low=1, high=5, size=1)[0]

        if o != d:
            if not [deadlinetime, weight, f_time] in all_task_details:

                all_task_details.append([deadlinetime, weight, f_time])

                while layer < maxlayer:
                    if (o, d) not in L_tasks[layer].keys():
                        # also check for every layer if time for that key has been taken
                        L_tasks[layer][o, d] = [deadlinetime, weight, f_time]
                        break

                    layer += 1

                layer = 0

    return L_tasks


def construct_matrix_flighttime(n):
    flighttime = np.empty((n+1,n+1))
    for i in range(n+1):
        for j in range(i+1,n+1):
                flighttime[i, j] = np.random.randint(low=1, high=10, size=1)[0]
                flighttime[j, i] = flighttime[i, j]
    return flighttime

def construct_airfraight_flighttime(C, C_task, C_fictive, flighttime, L_tasks):
    flighttime_case = np.empty((len(C), len(C)))
    C_task_mod = C_task[1:]
    for i in C_task_mod:
        flighttime_case[i, i + len(C_task_mod)] = 0
        flighttime_case[i + len(C_task_mod), i] = 0
    for i in C_task_mod:
        for j in C_task_mod:
            for k in range(len(L_tasks)):
                if (i,j) in L_tasks[k]:
                    flighttime_case[i, j] = flighttime[i, j]
    for i in C_fictive:
        for j in C_fictive:
            if i != j:
                flighttime_case[i, j] = flighttime[i - len(C_task_mod), j - len(C_task_mod)]
    for j in C_fictive:
        flighttime_case[0, j] = flighttime[0, j - len(C_task_mod)]
        flighttime_case[j, 0] = flighttime[j - len(C_task_mod), 0]
    return flighttime_case

def construct_airfraight_timeinterval_from_modified_tasks(L_tasks, timestep):
    # iterate through all task dictionaries
    max = 0
    # do as long list does not contain empty dict
    for k,v in L_tasks.items():
        if v[0] > max:
            max = v[0]

    T = np.arange(timestep, max+1, 1)
    return T

def construct_airfraight_timeinterval(L_tasks, timestep):
    # iterate through all task dictionaries
    max = 0
    layer = 0
    while L_tasks[layer]: # do as long list does not contain empty dict
        for k,v in L_tasks[layer].items():
            if v[0] > max:
                max = v[0]
        layer += 1

    T = np.arange(timestep, max+1, 1)
    return T


def make_fixed_airfraight_inst(timeinterval):
    # L list of tasks with one flight
    L_task = dict()
    L_task[0, 1] = [2, 80, 1]
    #äL_task[2, 0] = [2, 200, 1]
    #L_task[2, 0] = [2, 100, 1]


    # generate dict for fleet
    F = construct_airfraight_fleet(1)
    C = construct_airfraight_cities(L_task)
    L_fictive = construct_fictive_flights(L_task, C)
    L = {**L_task, **L_fictive}
    cost = construct_airfraight_costs(L,F,timeinterval)
    return L, L_task, C, F, cost



def construct_airfraight_fleet(size=2):
    # genereate fleet
    fdict = dict()
    for i in range(size):
        if i == 0:
            w_max = 250
            t_max = 200
            tank_max = 3
            fdict[i] = [w_max, t_max,tank_max]
        if (i < 8 and i > 0):
            w_max = 150
            t_max = 200
            tank_max = 6
            fdict[i] = [w_max, t_max,tank_max]
        if i == 8:
            w_max = 60
            t_max = 200
            tank_max = 11
            fdict[i] = [w_max, t_max,tank_max]
        if i == 9:
            w_max = 5.5
            t_max = 200
            tank_max=3
            fdict[i] = [w_max, t_max,tank_max]
        if i >= 9:
            w_max = 250
            t_max = 200
            tank_max = 3
            fdict[i] = [w_max, t_max, tank_max]

    return fdict

def construct_airfraight_cities(L_tasks, num_cities):
    # genereate list of cities based on L
    C = [0]
    C_temp = [0]
    L_tasks_modified = dict()
    layer = 0
    while L_tasks[layer]:
        for k, v in L_tasks[layer].items():
            if k[0] + num_cities*(layer) not in C:
                C.append(k[0] + num_cities*(layer))
                C_temp.append(k[0])
            if k[1] + num_cities*(layer) not in C:
                C.append(k[1] + num_cities*(layer))
                C_temp.append(k[1])
            L_tasks_modified[k[0] + num_cities*(layer), k[1] + num_cities*(layer)] = v
        layer += 1
    return list(np.sort(C)), L_tasks_modified

def construct_airfraight_cities_fictive(L_tasks, C_task, num_cities):
    # C_fictive includes all cities that are tasks
    # If we have the an empty task list
    num_layers = len([i for i in range(len(L_tasks)) if L_tasks[i]])
    if num_layers != 0:
        C_mod = C_task[1:int(len(C_task[1:])/num_layers + 1)]
        C_fictive = []

        for i in C_mod:
            C_fictive.append(i + num_layers*num_cities)
        return C_fictive
    else:
        return []

def construct_possible_flights(flight_time_matrix, C_fictive, C_task, L_tasks, num_cities):

    num_layers = len([i for i in range(len(L_tasks)) if L_tasks[i]])
    L_fictive = dict()
    C_mod = [0] + C_fictive

    for o in C_mod:
        for d in C_mod:
            if o == d:
                continue
            else:
                if o == 0:
                    L_fictive[o, d] = [1000000, 0, flight_time_matrix.flighttime[o ,d - num_cities * num_layers]]
                elif d == 0:
                    L_fictive[o, d] = [1000000, 0, flight_time_matrix.flighttime[o - num_cities * num_layers,d]]
                else:
                    L_fictive[o, d] = [1000000, 0, flight_time_matrix.flighttime[o - num_cities * num_layers,d - num_cities * num_layers]]

    for x in range(1, num_layers+1):
        for i in C_fictive:
            L_fictive[i, i - x * num_cities] = [1000000, 0, 0]
            L_fictive[i - x * num_cities, i] = [1000000, 0, 0]
    return L_fictive

def construct_airfraight_costs(L,F, T):
    # genereate dictionary for cost of each flight for each aircraft
    cost = dict()
    for f in F:
        for t in T:
            for k, v in L.items():
                cost[f, k[0], k[1], t] = (F[f][0]-v[1])*v[2]
    return cost

def construct_fictive_flights(L, C):
    L_fictive = dict()
    for o in C:
        for d in C:
            if (o,d) in L.keys():
                continue
            elif o == d:
                continue
            else:
                L_fictive[o,d] = [1000000, 0, 1]
    return L_fictive

if __name__ == "__main__":
    flighttime = construct_matrix_flighttime(100)
    print(flighttime)
    C = [0, 1, 2, 3, 4]
    C_task = [0, 1, 2]
    C_fictive = [3, 4]
    flighttime_case = construct_airfraight_flighttime(C, C_task, C_fictive, flighttime)
    print(flighttime_case)
