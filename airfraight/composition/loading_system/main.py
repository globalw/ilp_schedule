"""
a model for the loading system problem

Model for solving a loading system problem:
minimize the total transportation cost of the loading systems satisfying the scheduled flights

input - x(f,o,d,t) (airplaine f flies from o to d with departure time t)
      - nxn matrix flighttime (entry (o,d) gives flighttime from o to d)
"""

import airfraight.loading_system.gen_data_loading_systems as loading_gen_data
import airfraight.loading_system.gen_data_input as input
import composition.model_loading_systems as model

if __name__ == "__main__":
    # this particular run goes from time 0
    timestep = 0

    flight_variables, L_tasks = input.gen_data_input()

    flighttime = loading_gen_data.construct_matrix_flighttime(100)
    loadingsystems = loading_gen_data.construct_airfraight_loadindsystems(2)
    # TODO can be taken from composition.gen_data_fix --> DO IT!
    T = loading_gen_data.construct_airfraight_timeinterval(L_tasks)
    # TODO can be taken from composition.gen_data_fix --> DO IT!
    C_task = loading_gen_data.construct_airfraight_cities(L_tasks)
    # TODO can be taken from composition.gen_data_fix --> DO IT!
    C_fictive = loading_gen_data.construct_airfraight_cities_fictive(C_task)
    C = C_task + C_fictive
    LS_start = input.construct_airfraight_LS_start(loadingsystems, C_task)

    # TODO here we mean the fligth_time_matrix.... get it from the appropriate place
    flighttime_case = loading_gen_data.construct_airfraight_flighttime(C, C_task, C_fictive, flighttime, L_tasks)
    transp_time_ls = loading_gen_data.construct_airfraight_transp_loadingsystems(C_fictive, C_task, C, flighttime_case)
    cost = loading_gen_data.construct_loadingsystem_costs(transp_time_ls, loadingsystems, T)

    print(C_task)
    print(C_fictive)
    print(L_tasks)
    print(transp_time_ls)
    print(flight_variables)
    print(loadingsystems)
    print(LS_start)

    model = model.transp_loadingsystems(loadingsystems, flight_variables, L_tasks, T, C, transp_time_ls, LS_start, cost)
    model.optimize()

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    a, b = model.data

    for j in a:
        if model.getVal(a[j]) > EPS:
            print(a[j].name, "=", model.getVal(a[j]))

    for j in b:
        if model.getVal(b[j]) > EPS:
            print(b[j].name, "=", model.getVal(b[j]))

