import socket
import multiprocessing as mp
import numpy as np
import airfraight.composition.gen_data_fix as fleet_gen_data
import airfraight.loading_system.gen_data_loading_systems as loading_gen_data
import composition.model_loading_systems as ldm
import airfraight.loading_system.gen_data_input as input
import airfraight.composition.simulation as sim
import airfraight.composition.utils as af
import ast
import time
import pickle
import copy

def read_random_fleet_input_instance(file_path):

    # we open the file for reading
    fileObject = open(file_path, 'r')
    # load the object from the file into var b
    data = []
    with open(file_path, "rb") as f:
        for _ in range(pickle.load(f)):
            data.append(pickle.load(f))

    return data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]

def read_random_loading_input_instance(file_path):

    # we open the file for reading
    fileObject = open(file_path, 'r')
    # load the object from the file into var b
    data = []
    with open(file_path, "rb") as f:
        for _ in range(pickle.load(f)):
            data.append(pickle.load(f))

    return data[0], data[1]

def server_program(sharedMem, host, port):
    server_socket = socket.socket()  # get instance
    # make available for rebinding
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # look closely. The bind() function takes tuple as argument
    server_socket.bind((host, port))  # bind host address and port together

    # configure how many client the server can listen simultaneously
    server_socket.listen(2)
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))
    while True:
        # receive data stream. it won't accept data packet greater than 1024 bytes
        data = conn.recv(1024).decode()
        if not data:
            # if data is not received break
            break

        returndata = check_for_commands(sharedMem, data)
        print("from connected user: " + str(data))
        print("server answer: " + check_for_commands(sharedMem, data))
        conn.send(returndata.encode())# send data to the client

        #termination signal
        if sharedMem['terminate']:
            break

    conn.close()  # close the connection

def check_for_commands(sharedMem,data):
    # here we basicall check the received message and execute the simulation
    # data is a string that needs to be interpreted
    commandArr = str(data).split(' ')
    message = ''
    try:
        if (commandArr[0] == 'opt'):
            if(commandArr[1] == 'true'):
                sharedMem['optimise'] = True
                message = 'optimisation switched on!'
            elif(commandArr[1] == 'false'):
                sharedMem['optimise'] = False
                message = 'switch off optimisation'
            else:
                message = 'could not understand the optimisation command...retry!'


        elif(commandArr[0] == 'task'):
            message = 'You told us to insert a new task. We will do that. We will \n'+ \
                  'take some time to optimize the problem and the geive you the \n'+ \
                  'schedule you need'

            if commandArr[2] == 'done':
                message = str(sharedMem['L_done'])
            elif commandArr[2] == 'undone':
                message = str(sharedMem['L_tasks'])
            elif commandArr[1] == 'integrate':
                # translate the input form string to dictionary
                if type(ast.literal_eval(commandArr[2])) == dict:
                    message = task_integrate(commandArr[2], sharedMem)
                else:
                    message = 'The format of the task is incorrect'
            else:
                message = 'Task message could not be understood.'


        elif (commandArr[0] == 'simulate'):
            if(commandArr[1] == 'true'):
                sharedMem['simulate'] = True
                message = 'You told us to start the simulation. Simulation starting...'
            elif (commandArr[1] == 'false'):
                sharedMem['simulate'] = False
                message = 'You told us to stop the simulation. Aborting Simulation...'
            else:
                message = 'Simulate and then what? We dont understand'
        elif commandArr[0] == 'shutdown':
            message = 'shutting down airfraight server... good bye!'
            sharedMem['terminate'] = True
        else:
            message = 'We dont understand'
    except Exception:
        message = 'Please dont forget the command syntax'

    return message

def task_integrate(stringtask, sharedMem):
    # basically we only need to go through the indices of the given task
    # and put them into the ones we all ready have. This excludes the ones
    # we have delivered to the current time or are being delivered.
    maxlayer = 20
    timestep = sharedMem['timestep']
    new_tasks = ast.literal_eval(stringtask)

    updatedTasks = dict()
    #to make things simple we simply make a household of finished jobs and
    # unfinished jobs.

    tasks_added = 0
    last_absolute_time = 1000000 # should be corrected
    task_add_attempt = 0
    for (i, j) in new_tasks:
        task_add_attempt += 1
        if new_tasks[i, j][0] > timestep:
            # if loading time and minimum travelling time added together
            # are less than the provided timeinterval on which to solve it
            # we have to issue the warning that the task ist not suffiecient
            if last_absolute_time < new_tasks[i, j][2] + 1: # note we add 1 for the minimum traveling time because we dont know better
                print('the task cannot be fullfilled on the given interval')

            tasks_added += 1
            updatedTasks[i, j] = new_tasks[i, j]

    # add the tasks to the L_tasks shared memory by doing the same thing like in simulation.py
    # we write the shared memory tasks to a local list of dictionaries and
    L_tasks = sharedMem['L_tasks']
    L_tasks_copy = copy.copy(L_tasks)
    num_cities = sharedMem['num_cities']

    # find the fist layer that does not contain the updated task key
    for k in updatedTasks:
        layer = 0
        while layer < maxlayer:
            if k not in L_tasks_copy[layer].keys():
                L_tasks_copy[layer][k] = updatedTasks[k]
                break
            layer += 1

    sharedMem['L_tasks'] = L_tasks_copy


    # recalculate all necesseray variables in the shared memory L, C, cost
    # num_cities is a constant number!
    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, T, flight_time_matrix, cost = \
        fleet_gen_data.update_airfraight_inst(L_tasks, sharedMem['fleet'], timestep, num_cities,
                                        sharedMem['flighttimematrix'])

    print('Updating shared memory...')
    sharedMem['L'] = L
    sharedMem['L_tasks'] = L_tasks
    sharedMem['L_tasks_modified'] = L_tasks_modified
    sharedMem['C'] = C
    sharedMem['C_fictive'] = C_fictive
    sharedMem['C_task'] = C_task
    sharedMem['timeinterval'] = T
    sharedMem['costgraph'] = cost
    sharedMem['num_citites'] = num_cities
    sharedMem['flighttimematrix'] = flight_time_matrix

    if np.abs(tasks_added-task_add_attempt) == 0:
        message = 'all tasks have been added. Please run \n' \
                  'optimisation in order to get the new \n' \
                  'schedule'
    else:
        message = 'one or more tasks have not been added due to time discrepancies.'
    # overwrite

    return message

def generate_and_pickle_fleet_test_data(tasksize, num_cities, file_path):

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        fleet_gen_data.make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities)
    data = [L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost]

    with open(file_path, "wb") as f:
        pickle.dump(len(data), f)
        for value in data:
            pickle.dump(value, f)

def save_data_to_file(tasksize, num_cities, data, file_path):
    with open(file_path, "wb") as f:
        pickle.dump(len(data), f)
        for value in data:
            pickle.dump(value, f)

def generate_and_pickle_loading_test_data(numloadingsystems, loading_C_task, file_path):
    loadingsystems = loading_gen_data.construct_airfraight_loadindsystems(numloadingsystems)
    LS_start = input.construct_airfraight_LS_start(loadingsystems, loading_C_task)
    data = [loadingsystems, LS_start]

    with open(file_path, "wb") as f:
        pickle.dump(len(data), f)
        for value in data:
            pickle.dump(value, f)

def run_airfraight_optimisation_server(host, port):
    # the server is basically a parser of messages from the client. Lets say
    # the client wants to start the simulation. The server runs in a thread.
    # If the 'simulate' command was send by the client, the server writes a
    # boolean to the according place of the shared memory.

    #tasksize = 10
    #num_cities = 55
    #L, L_tasks, L_task_modified, C, F, T, ftm, cost = gen_data.make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities)
    # L, C, F, cost = gen_data.make_random_airfraight_inst(fleetsize=10, flights=2, number_cities=3,
    #                                        timeinterval=timeinterval)

    ############# solving for fleet schedule ######################
    #tasksize = 5
    num_cities = 50
    #numloadingsystems = 10

    #fleettestcase1 = "fleettestsize_10_num_cities.inst"
    #fleettestcase2 = "fleetsize_10_num_cities_10_tasksize_40.inst"
    fleettestcase3 = "fleetsize_10_num_cities_50_tasksize_5.inst"
    #fleettestcase4 = "testdata.inst"

    #generate_and_pickle_fleet_test_data(tasksize, num_cities, "data/"+fleettestcase3)

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        read_random_fleet_input_instance("data/" + fleettestcase3)

    #loadingtestcase1 = "tasksize_10_num_cities 20.inst"
    loadingtestcase2 = "task_size_5_num_cities_50.inst"
    #loadingtestcase3 = "testdata.inst"
    #loadingtestcase4 = "testdata.inst"

    #generate_and_pickle_loading_test_data(numloadingsystems, C_task, "data/"+ loadingtestcase2)
    timestep = 0.0
    loadingsystems, LS_start = read_random_loading_input_instance("data/" + loadingtestcase2)
    orig_flight_time_matrix = flight_time_matrix
    for loadingtimeoffset in np.arange(0,100,80):
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

    #for j in a:
    #   if loadingmodel.getVal(a[j]) > EPS:
    #       print(a[j].name, "=", model.getVal(a[j]))

    #for j in b:
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
               'C_ficitve': C_fictive,
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
    #server_program(sharedMem, host, port)
    ##### initialize server process ############
    # get the hostname
    #host = socket.gethostname()
    #port = 5000# initiate port no above 1024
    serverprocess = mp.Process(target=server_program, args=(sharedMem, host, port))
    serverprocess.start()
    print('server started...')
    jobs.append(serverprocess)
    ############################################

    # simulation thead is also this thread...

    #sim.simulation(sharedMem)
    ##### initialize simulation process ########
    simulationprocess = mp.Process(target=sim.simulation, args=(sharedMem,))
    simulationprocess.start()
    print('simulation started...')
    #jobs.append(simulationprocess)
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

if __name__ == '__main__':

    host = socket.gethostname()
    port = 5000# initiate port no above 1024


    run_airfraight_optimisation_server(host, port)
