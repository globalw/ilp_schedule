import numpy as np
import airfraight.composition.gen_data_fix as fleet_gen_data
import airfraight.composition.utils as af
import airfraight.composition.server as server
import time
import pickle
import multiprocessing as mp
import matplotlib.pyplot as plt

def read_runtimes(file_path):

    # we open the file for reading
    fileObject = open(file_path, 'r')
    # load the object from the file into var b
    data = []
    with open(file_path, "rb") as f:
        for _ in range(pickle.load(f)):
            data.append(pickle.load(f))

    return data[0], data[1]

def generate_and_pickle_fleet_test_data(tasksize, num_cities, file_path):

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        fleet_gen_data.make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities)
    data = [L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost]

    with open(file_path, "wb") as f:
        pickle.dump(len(data), f)
        for value in data:
            pickle.dump(value, f)

def parallel_airfreight_schedule_runtime(resultfilepath):
    tasksizemin = 2
    tasksizemax = 20
    manager = mp.Manager()
    feasabletime = {k: [] for k in np.arange(tasksizemin, tasksizemax)}
    sharedMem = manager.dict(feasabletime)
    jobs = []
    for tasksize in np.arange(tasksizemin, tasksizemax, 2):
        process = mp.Process(target=mp_airfreight_schedule_runtime, args=(sharedMem, tasksize, tasksize + 1, resultfilepath))
        #mp_airfreight_schedule_runtime(sharedMem, tasksize, tasksize + 1, resultfilepath)
        process.start()
        print('process with tasksize min '+str(tasksize)+' started...')
        jobs.append(process)

    # join the thread
    for j in jobs:
        j.join()

    avtimes = []
    for k in dict(sharedMem).keys():
        avtimes.append(np.sum(dict(sharedMem)[k]))

    plt.plot(avtimes)
    plt.show()
    #write_shared_mem_result_to_file(resultfilepath, sharedMem)
    read_result(resultfilepath)

def write_shared_mem_result_to_file(resultfilepath, sharedMem):
    noproxydict = dict(sharedMem)
    with open(resultfilepath, "wb") as f:
        pickle.dump(len(noproxydict), f)
        for value in noproxydict:
            pickle.dump(value, f)

def read_result(resultfilepath):
    # we open the file for reading

    # load the object from the file into var b
    data = []
    with open(resultfilepath, 'rb') as f:
        for _ in range(pickle.load(f)):
            data.append(pickle.load(f))

    return data

def mp_airfreight_schedule_runtime(feasabletime, tasksizemin, tasksizemax, resultfilepath):
    num_cities = 100
    #tasksizemin = 2
    #tasksizemax = 20
    numloadingsystems = 10
    numofsamples = 20

    feasablecount = 0
    infeasablecount = 0

    infeasabletime = {k: [] for k in np.arange(tasksizemin, tasksizemax + 1)}


    for tasksize in np.arange(tasksizemin, tasksizemax + 1):
        samplenum = 0
        while samplenum < numofsamples:

            fleettestcase = "fleettestsize_10_num_cities_" + str(num_cities) + "_tasksize_" + str(tasksize) + ".inst"

            generate_and_pickle_fleet_test_data(tasksize, num_cities, "runtimecomplexitycases/" + fleettestcase)

            L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
                server.read_random_fleet_input_instance("runtimecomplexitycases/" + fleettestcase)

            timestep = 0.0
            loadingtimeoffset = 0.0
            fleet_gen_data.adjust_airfraight_inst_with_loadingtime_offset(L_tasks, F, timestep, num_cities,
                                                                          loadingtimeoffset,
                                                                          flight_time_matrix.flighttime)

            starttime = time.time()
            model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, num_cities)
            model.optimize()
            endtime = time.time()

            comptime = endtime - starttime

            # if model.getStatus() == 'infeasable' and infeasablecount <= numofsamples / 2:
            #     infeasabletime[tasksize].append(comptime / numofsamples)
            #     infeasablecount += 1
            #     samplenum += 1

            if model.getStatus() == 'optimal': # and feasablecount <= numofsamples / 2:
                # feasabletime is dictProxy
                templist = list(feasabletime[tasksize])
                templist.append(comptime / numofsamples)

                feasabletime[tasksize] = templist

                feasablecount += 1
                samplenum += 1

            print("Optimal value:", model.getObjVal())

def airfreight_schedule_runtime(resultfilepath):
    num_cities = 100
    tasksizemin = 2
    tasksizemax = 20
    numloadingsystems = 10
    numofsamples = 20

    feasablecount = 0
    infeasablecount = 0

    infeasabletime = {k: [] for k in np.arange(tasksizemin, tasksizemax + 1)}
    feasabletime = {k: [] for k in np.arange(tasksizemin, tasksizemax + 1)}

    for tasksize in np.arange(tasksizemin, tasksizemax + 1):
        samplenum = 0
        while samplenum < numofsamples:

            fleettestcase = "fleettestsize_10_num_cities_" + str(num_cities) + "_tasksize_" + str(tasksize) + ".inst"

            generate_and_pickle_fleet_test_data(tasksize, num_cities, "runtimecomplexitycases/" + fleettestcase)

            L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
                server.read_random_fleet_input_instance("runtimecomplexitycases/" + fleettestcase)

            timestep = 0.0
            loadingtimeoffset = 0.0
            fleet_gen_data.adjust_airfraight_inst_with_loadingtime_offset(L_tasks, F, timestep, num_cities,
                                                                          loadingtimeoffset,
                                                                          flight_time_matrix.flighttime)

            starttime = time.time()
            model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, num_cities)
            model.optimize()
            endtime = time.time()

            comptime = endtime - starttime

            # if model.getStatus() == 'infeasable' and infeasablecount <= numofsamples / 2:
            #     infeasabletime[tasksize].append(comptime / numofsamples)
            #     infeasablecount += 1
            #     samplenum += 1

            if model.getStatus() == 'optimal': #and feasablecount <= numofsamples / 2:
                feasabletime[tasksize].append(comptime / numofsamples)
                feasablecount += 1
                samplenum += 1

            print("Optimal value:", model.getObjVal())

    with open(resultfilepath, "wb") as f:
        pickle.dump(infeasabletime, f)
        pickle.dump(feasabletime, f)

if __name__== '__main__':
    resultfilepath = "runtimecomplexitycases/results.dat"

    #airfreight_schedule_runtime(resultfilepath)
    parallel_airfreight_schedule_runtime(resultfilepath)