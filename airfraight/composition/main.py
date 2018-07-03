import airfraight.composition.utils as af
import airfraight.composition.gen_data_fix as fleet_gen_data

import airfraight.composition.loading_system.gen_data_loading_systems as loading_gen_data
import airfraight.composition.loading_system.gen_data_input as input
import airfraight.composition.model_loading_systems as ldm

import pickle


def generate_and_pickle_fleet_test_data(tasksize, num_cities, file_path):

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        fleet_gen_data.make_fixed_airfraight_inst_by_tasksize(tasksize, num_cities)
    data = [L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost]

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

def run_fleet_schedule_test():

    tasksize = 5
    num_cities = 20

    #generate_and_pickle_fleet_test_data(tasksize, num_cities, "data/tasksize_5_num_cities 20.inst")

    testcase1 = "tasksize_5_num_cities 20.inst"
    testcase2 = "testdata.inst"
    testcase3 = "testdata.inst"
    testcase4 = "testdata.inst"
    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = read_random_loading_input_instance("data/" + testcase1)

    print(L)
    print(L_tasks)
    print(L_tasks_modified)
    print(C)
    print(C_task)
    print(C_fictive)
    print(F)
    print(T)
    print(flight_time_matrix)
    print(cost)

    model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, cost)
    model.optimize()

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    x, y, z = model.data
    for j in x:
        if model.getVal(x[j]) > EPS and (x[j].name[2] == "9" or x[j].name[2] == "4" ):
            print(x[j].name, "=", model.getVal(x[j]))
    for j in y:
        if model.getVal(y[j]) > EPS and (y[j].name[2] == "9" or y[j].name[2] == "4" ):
            print(y[j].name, "=", model.getVal(y[j]))
    for j in z:
        if model.getVal(z[j]) > EPS and (z[j].name[2] == "9" or z[j].name[2] == "4" ):
            print(z[j].name, "=", model.getVal(z[j]))

    flighttime_matrix={}
    return model, L, L_tasks_modified, C, F, cost, flighttime_matrix

def run_fleet_loading_schedule_test():
    ############# solving for fleet schedule ######################
    tasksize = 5
    num_cities = 20
    numloadingsystems = 10

    #generate_and_pickle_fleet_test_data(tasksize, num_cities, "data/fleettestsize_10_num_cities.inst")

    fleettestcase1 = "fleettestsize_10_num_cities.inst"
    fleettestcase2 = "testdata.inst"
    fleettestcase3 = "testdata.inst"
    fleettestcase4 = "testdata.inst"

    L, L_tasks, L_tasks_modified, C, C_task, C_fictive, F, T, flight_time_matrix, cost = \
        read_random_fleet_input_instance("data/" + fleettestcase1)

    loadingtestcase1 = "tasksize_10_num_cities 20.inst"
    loadingtestcase2 = "testdata.inst"
    loadingtestcase3 = "testdata.inst"
    loadingtestcase4 = "testdata.inst"

    #generate_and_pickle_loading_test_data(numloadingsystems, C_task, "data/"+ loadingtestcase1)

    loadingsystems, LS_start = read_random_loading_input_instance("data/" + loadingtestcase1)

    print(L)
    print(L_tasks)
    print(L_tasks_modified)
    print(C)
    print(C_fictive)
    print(F)
    print(T)
    print(flight_time_matrix)
    print(cost)

    model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, num_cities)
    model.optimize()

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    x, y, z = model.data
    for j in x:
        if model.getVal(x[j]) > EPS:# and (x[j].name[2] == "9" or x[j].name[2] == "4" ):
            print(x[j].name, "=", model.getVal(x[j]))
    for j in y:
        if model.getVal(y[j]) > EPS:# and (y[j].name[2] == "9" or y[j].name[2] == "4" ):
            print(y[j].name, "=", model.getVal(y[j]))
    for j in z:
        if model.getVal(z[j]) > EPS:# and (z[j].name[2] == "9" or z[j].name[2] == "4" ):
            print(z[j].name, "=", model.getVal(z[j]))

    flighttime_matrix = {}



    ################### solving for loading system schedule ########################

    # at this point we have a lot of the data structures at hand that we produced for the
    # optimisation run before

    timestep = 0
    # we need to construct the "flight_variables" according to the solution of the fleet_scheduling
    # problem. Then according Tasks are build. For the beginning we specifiy the loadingtimeoffset
    # and try to find a solution. If no solution is found wie increase the offset until we find
    # a solution
    #flight_variables, L_loading_tasks = input.gen_data_input()
    for loadingtimeoffset in range(20):
        flight_variables, loading_L_tasks = input.gen_loading_data_input(model, L_tasks_modified, loadingtimeoffset)

        # flighttime = loading_gen_data.construct_matrix_flighttime(100)
        # TODO can be taken from composition.gen_data_fix --> DO IT!... Done?
        loading_T = fleet_gen_data.construct_airfraight_timeinterval_from_modified_tasks(loading_L_tasks, timestep)
        # TODO can be taken from composition.gen_data_fix --> DO IT!... Done?
        loading_C_task = loading_gen_data.construct_airfraight_cities(loading_L_tasks)
        # TODO can be taken from composition.gen_data_fix --> DO IT!... Done?
        loading_C_fictive = loading_gen_data.construct_airfraight_cities_fictive(loading_C_task)
        loading_C = loading_C_task + loading_C_fictive
        #LS_start = input.construct_airfraight_LS_start(loadingsystems, loading_C_task)
        # TODO here we mean the fligth_time_matrix.... get it from the appropriate place... do we need this? It is
        # TODO all ready there...
        #flighttime_case = loading_gen_data.construct_airfraight_flighttime(loading_C, loading_C_task, loading_C_fictive,
        #                                                                   flight_time_matrix.flighttime, loading_L_tasks)

        # enter the method for better overview. The input for C_fictive is the full city list with fictive cities
        # task cities and all the cities in beteween. This is because we are accessing the flighttime(-matrix) by indizes
        # contained in this full list
        C_full = [i for i in range(0,num_cities+1)]
        transp_time_ls = loading_gen_data.construct_airfraight_transp_loadingsystems(C_full, loading_C_task,
                                                                                     loading_C, flight_time_matrix.flighttime)
        # TODO attention the traversing time for cities that do not have task is zero...does this cause problems?
        loading_cost = loading_gen_data.construct_loadingsystem_costs(transp_time_ls, loadingsystems, loading_T)

        print(loading_C_task)
        print(loading_C_fictive)
        print(loading_L_tasks)
        print(transp_time_ls)
        print(flight_variables)
        print(loadingsystems)
        print(LS_start)

        loadingmodel = ldm.transp_loadingsystems(loadingsystems, flight_variables, loading_L_tasks, loading_T, loading_C,
                                            transp_time_ls, LS_start, loading_cost)
        loadingmodel.optimize()
        if loadingmodel == True:
            # solution was found
            break

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    a, b = loadingmodel.data

    for j in a:
        if loadingmodel.getVal(a[j]) > EPS:
            print(a[j].name, "=", model.getVal(a[j]))

    for j in b:
        if loadingmodel.getVal(b[j]) > EPS:
            print(b[j].name, "=", model.getVal(b[j]))

    return loadingmodel, L, L_tasks_modified, C, F, cost, flighttime_matrix

if __name__ == "__main__":

    #model, L, L_tasks_modified, C, F, cost, flight_time_matrix = run_fleet_schedule_test()

    model, L, L_tasks_modified, C, F, cost, flight_time_matrix = run_fleet_loading_schedule_test()
    #mls.transp_loadingsystems(flighttime_matrix, loadingsystems, , L_tasks, T, C, transp_time_ls,
    #                          LS_start, cost)
