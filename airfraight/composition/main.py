import socket
import multiprocessing as mp
import numpy as np
import airfraight.composition.gen_data_fix as fleet_gen_data
import airfraight.composition.loading_system.gen_data_loading_systems as loading_gen_data
import airfraight.composition.loading_system.model_loading_systems as ldm
import airfraight.composition.loading_system.gen_data_input as input
import airfraight.composition.simulation as sim
import airfraight.composition.utils as af
import airfraight.composition.server as server
import time
import pickle
import copy

def run_airfraight_optimisation_server(host, port):
    # the server is basically a parser of messages from the client. Lets say
    # the client wants to start the simulation. The server runs in a thread.
    # If the 'simulate' command was send by the client, the server writes a
    # boolean to the according place of the shared memory.

    # tasksize = 10
    # num_cities = 55
    # L, L_tasks, L_task_modified, C, F, T, ftm, cost = gen_data.make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities)
    # L, C, F, cost = gen_data.make_random_airfraight_inst(fleetsize=10, flights=2, number_cities=3,
    #                                        timeinterval=timeinterval)

    ############# solving for fleet schedule ######################
    # tasksize = 5
    num_cities = 50
    # numloadingsystems = 10

    # fleettestcase1 = "fleettestsize_10_num_cities.inst"
    # fleettestcase2 = "fleetsize_10_num_cities_10_tasksize_40.inst"
    fleettestcase3 = "fleetsize_10_num_cities_50_tasksize_5.inst"
    # fleettestcase4 = "testdata.inst"

    # generate_and_pickle_fleet_test_data(tasksize, num_cities, "data/"+fleettestcase3)

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        server.read_random_fleet_input_instance("data/" + fleettestcase3)

    # loadingtestcase1 = "tasksize_10_num_cities 20.inst"
    loadingtestcase2 = "task_size_5_num_cities_50.inst"
    # loadingtestcase3 = "testdata.inst"
    # loadingtestcase4 = "testdata.inst"

    # generate_and_pickle_loading_test_data(numloadingsystems, C_task, "data/"+ loadingtestcase2)
    timestep = 0.0
    loadingsystems, LS_start = server.read_random_loading_input_instance("data/" + loadingtestcase2)
    orig_flight_time_matrix = flight_time_matrix
    for loadingtimeoffset in np.arange(0, 100, 80):
        # here we  adjust the loadingtimeoffset with the tasks. What we need to do
        # is simply to add the loading timeoffset to the flight time... since we
        # agreed on the flightime matrix object. the adjustment should be only
        # there.
        fleet_gen_data.adjust_airfraight_inst_with_loadingtime_offset(L_tasks, F, timestep, num_cities,
                                                                      loadingtimeoffset, flight_time_matrix.flighttime)

        model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, num_cities)
        model.optimize()

        print("Optimal value:", model.getObjVal())

        EPS = 1.e-6
        x, y, z = model.data
        for j in x:
            if model.getVal(x[j]) > EPS:
                print(x[j].name, "=", model.getVal(x[j]))
        for j in y:
            if model.getVal(y[j]) > EPS:
                print(y[j].name, "=", model.getVal(y[j]))
        for j in z:
            if model.getVal(z[j]) > EPS:
                print(z[j].name, "=", model.getVal(z[j]))

        flighttime_matrix = {}

        ################### solving for loading system schedule ########################

        timestep = 0

        flight_variables, loading_L_tasks = input.gen_loading_data_input(model, L_tasks_modified, loadingtimeoffset)

        loading_T = fleet_gen_data.construct_airfraight_timeinterval_from_modified_tasks(loading_L_tasks, timestep)
        loading_C, loading_C_task, loading_C_ficitve = loading_gen_data.construct_airfraight_cities(L_tasks, num_cities,
                                                                                                    flight_time_matrix.flighttime)

        transp_time_ls = loading_gen_data.construct_airfraight_transp_loadingsystems(L)

        loading_cost = loading_gen_data.construct_loadingsystem_costs(transp_time_ls, loadingsystems, loading_T)

        loadingmodel = ldm.transp_loadingsystems(loadingsystems, flight_variables, loading_L_tasks, loading_T,
                                                 loading_C,
                                                 transp_time_ls, LS_start, loading_cost)
        loadingmodel.optimize()
        if loadingmodel == True:
            # solution was found
            break

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    a, b = loadingmodel.data

    # for j in a:
    #   if loadingmodel.getVal(a[j]) > EPS:
    #       print(a[j].name, "=", model.getVal(a[j]))

    # for j in b:
    #    if loadingmodel.getVal(b[j]) > EPS:
    #        print(b[j].name, "=", model.getVal(b[j]))

    print("Optimal value:", loadingmodel.getObjVal())

    # get the values out of the expressions
    x_val, y_val, z_val = af.write_opt_res_to_values(model)

    control = {'terminate': False,
               'optimise': False,
               'simulate': False,
               'timestep': 0.0,
               'timeinterval': T,
               'L': L,
               'L_tasks': L_tasks,
               'L_tasks_modified': L_tasks_modified,
               'L_done': dict(),
               'fleet': F,
               'C': C,
               'C_task': C_task,
               'C_fictive': C_fictive,
               'costgraph': cost,
               'num_cities': num_cities,
               'flighttimematrix': flight_time_matrix,
               'schedule_x': x_val,
               'schedule_y': y_val,
               'schedule_z': z_val,
               'loadingsystems': loadingsystems,
               'LS_start': LS_start}

    # shared memeory
    manager = mp.Manager()
    sharedMem = manager.dict(control)
    jobs = []

    # server thread is this thread....
    # server_program(sharedMem, host, port)
    ##### initialize server process ############
    # get the hostname
    # host = socket.gethostname()
    # port = 5000# initiate port no above 1024
    serverprocess = mp.Process(target=server.server_program, args=(sharedMem, host, port))
    serverprocess.start()
    print('server started...')
    jobs.append(serverprocess)
    ############################################

    # simulation thead is also this thread...

    # sim.simulation(sharedMem)
    ##### initialize simulation process ########
    simulationprocess = mp.Process(target=sim.simulation, args=(sharedMem,))
    simulationprocess.start()
    print('simulation started...')
    # jobs.append(simulationprocess)
    ############################################

    # join the thread
    for j in jobs:
        j.join()

    while True:
        # check if shutdown is issued
        time.sleep(5)
        if sharedMem['terminate']:
            # terminate all process
            print('shutting down...')
            for j in jobs:
                j.terminate()
            break

if __name__ == "__main__":
    host = socket.gethostname()
    port = 5000  # initiate port no above 1024
    run_airfraight_optimisation_server(host, port)