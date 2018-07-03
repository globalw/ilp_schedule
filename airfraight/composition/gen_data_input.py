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
    L_task[1, 2] = [25, 50, 1]
    L_task[3, 4] = [25, 50, 1]


    return flight_variables, L_task

def construct_airfraight_LS_start(loadingsystems, C_task):
    LS_start = dict()
    for l in loadingsystems:
        LS_start[l] = np.random.randint(low=1, high=len(C_task), size=1)[0]

    return LS_start


if __name__ == "__main__":
    gen_data_input()