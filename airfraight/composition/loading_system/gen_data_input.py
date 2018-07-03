"""This script sets up a list of operated flights.

   tasks   -   {(f,o,d,t):1, ...} (aircraft f flies from o to d at departure time t)
   L_tasks -   [{(o,d):[td,w,f_time],...},...] (as in optimisation of flight assignment problem)

"""
import numpy as np

def gen_data_input():
    flight_variables = dict()
    flight_variables[1, 0, 1, 0] = 1
    flight_variables[1, 1, 2, 12] = 1

    flight_variables[2, 0, 3, 0] = 1
    flight_variables[2, 3, 4, 24] = 1


    for k in flight_variables:
        print(k)

    L_task = dict()
    # these are random but according to the above flight variables
    L_task[1, 2] = [25, 50, 1]
    L_task[3, 4] = [25, 50, 1]

    return flight_variables, L_task

def gen_loading_data_input(model, L_task_modified, loadingtimeoffset):
    EPS = 1.e-6
    x, y, z = model.data
    filtered_flight_variables = dict()

    for j in x:
        if model.getVal(x[j]) > EPS and (j[1], j[2]) in L_task_modified:# and (x[j].name[2] == "9" or x[j].name[2] == "4" ):
            filtered_flight_variables[j] = 1

    L_loading_tasks_modified = dict()
    # these are random but according to the above flight variables
    for j in filtered_flight_variables:
        # check if loading system is required
        loadingsystemlift = loading_system_selector(L_task_modified[j[1], j[2]][1])[0]
        # only issue loading tasks if a loading system is required
        if loadingsystemlift != 0:
            taskdeadline = L_task_modified[j[1], j[2]][0]
            L_loading_tasks_modified[j[1], j[2]] = [taskdeadline + loadingtimeoffset, loadingsystemlift, 1]

    return filtered_flight_variables, L_loading_tasks_modified

def loading_system_selector(cargotons):
    # the input is the tons to if the aircraft to be transported
    # the output is [loading system weight performance, loading system weight]
    if cargotons > 30 and cargotons <= 50:
        return [50, 12.5]
    elif cargotons > 50 and cargotons <= 80:
        return [80, 20]
    elif cargotons > 80 and cargotons <= 110:
        return [110, 27.5]
    elif cargotons > 110 and cargotons <= 140:
        return [140, 35]
    elif cargotons > 140 and cargotons <= 170:
        return [170, 42.5]
    elif cargotons > 170 and cargotons <= 200:
        return [200, 50]
    elif cargotons > 200:
        return [250, 62.5]
    else:
    # dont forget: if the cargo is below 30 tons, no loading system is required
        return [0, 0]

def construct_airfraight_LS_start(loadingsystems, C_task):
    # this randomizes an initial position dictionary for the loading systems
    LS_start = dict()
    for l in loadingsystems:
        LS_start[l] = np.random.randint(low=1, high=len(C_task), size=1)[0]

    return LS_start

def randomize_loading_system_start(loadingsystems, cities):
    # this randomizes an initial position dictionary for the loading systems
    LS_start = dict()
    for l in loadingsystems:
        LS_start[l] = np.random.randint(low=1, high=len(cities), size=1)[0]

    return LS_start

if __name__ == "__main__":
    gen_data_input()