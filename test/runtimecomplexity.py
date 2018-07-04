import numpy as np
import airfraight.composition.gen_data_fix as fleet_gen_data
import airfraight.composition.utils as af
import airfraight.composition.server as server
import time
import pickle

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

    airfreight_schedule_runtime(resultfilepath)