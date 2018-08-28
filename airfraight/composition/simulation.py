from multiprocessing import Manager
from pyscipopt import Model
import time
import airfraight.composition.gen_data_fix as fleet_gen_data
import airfraight.composition.utils as af
import airfraight.composition.gen_data_fix as gen_data
import airfraight.composition.loading_system.gen_data_loading_systems as loading_gen_data
import airfraight.composition.loading_system.gen_data_input as input
import airfraight.composition.model_loading_systems as ldm
import airfraight.composition.utils as af
import numpy as np


#def timestep(x, T):
#    EPS = 1.e-6
#    for (f, o, d, t) in x:
#        if x[f, o, d, T] > EPS:
#            print("Flight %3s is goint from %3s to %3s at time %5s.\n"
#                  "Value of the decision variable is %10s" % (f, o, d, t))

# reading x_start, y_start from last optimization at time t
def read_ics(x, y, flight_time_matrix, num_cities, F, C, T):
    x_start = dict()
    y_start = dict()
    ftm = dict(np.ndenumerate(flight_time_matrix))
    optmodel = Model("reader")

    EPS = 1.e-6
    for (f,o,d,t) in x:
        if T > t:
            if optmodel.getVal(x[f, o, d, t]) > EPS:
                if (d % num_cities, o % num_cities) in ftm:
                    if t + flight_time_matrix[d % num_cities, o % num_cities] > T:
                        x_start[f, o, d, t] = 1
    for f in F:
        for o in C:
            if (f, o, T-0.5) not in y:
                y_start[f, o, T - 0.5] = 0
            elif (f, o, T-0.5) in y and y[f, o, T - 0.5] == 1:
                y_start[f, o, T - 0.5] = 1

    return x_start, y_start

def solve_optimisation_problem(sharedMem):

    L = sharedMem['L']
    L_tasks_modified = sharedMem['L_tasks_modified']
    C = sharedMem['C']
    C_fictive = sharedMem['C_fictive']
    F = sharedMem['fleet']
    T = sharedMem['timeinterval']
    #optmodel = sharedMem['optmodel']
    ftm = sharedMem['flighttimematrix']
    num_cities = sharedMem['num_cities']
    timestep = sharedMem['timestep']
    schedule_x = sharedMem['schedule_x']
    schedule_y = sharedMem['schedule_y']

    x_start, y_start = read_ics(schedule_x, schedule_y, ftm.flighttime, num_cities, F, C, timestep)

    model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, x_start, y_start, num_cities)

    model.optimize()

    print("Optimal value:", model.getObjVal())

    EPS = 1.e-6
    x, y, z = model.data
    print('writing to shared memory...')

    x_val, y_val, z_val = af.write_opt_res_to_values(model)
    sharedMem['schedule_x'] = x_val
    sharedMem['schedule_y'] = y_val
    sharedMem['schedule_z'] = z_val


    for j in x:
        if model.getVal(x[j]) > EPS:
            print(x[j].name, "=", model.getVal(x[j]))
    count = 0
    for j in y:
        if model.getVal(y[j]) > EPS:
            print(y[j].name, "=", model.getVal(y[j]))
    for j in z:
        if model.getVal(z[j]) > EPS:
            print(z[j].name, "=", model.getVal(z[j]))

    sharedMem['optimise'] = False
    # for (f, o, d, t) in x:
    #   if model.getVal(x[f, o, d, t]) > EPS:
    #      print("Flight %3s is goint from %3s to %3s at time %5s.\n"
    #           "Value of the decision variable is %10s" % (f,o,d,t, model.getVal(x[f,o,d,t])))




def do_timestep(sharedMemory, timestep):
    # finally we got our schedule and we want to print to the
    # console what planes are going to a given time t
    EPS = 1.e-6
    fod = [i[0:3] for i in sharedMemory['schedule_x'] if i[3] == timestep]
    for (f, o, d) in fod:
        # all entries of the schedule are bigger EPS... never the less...
        if sharedMemory['schedule_x'][f, o, d, timestep] > EPS:
            # lets also check if the flight is carrying out a task
            if ((o, d) in sharedMemory['L_tasks_modified']):

                # is the flight a task route?

                # the task is being carried out and must be added to the
                # L_done list in  the shared memory
                # we modify L_tasks, not L_tasks_modified in order to construct a new
                # L_tasks_modified

                L_tasks = sharedMemory['L_tasks']
                num_cities = sharedMemory['num_cities']

                layer = int(np.floor(o/num_cities))
                olocal = (o % num_cities)
                dlocal = d % num_cities


                # create temp variables even is bad style
                tmp1 = dict()
                # write old entries of L_done into temp variable
                for done_keys in sharedMemory['L_done']:
                    tmp1[done_keys] = sharedMemory['L_done'][done_keys]

                originallayer = layer
                while (olocal, dlocal) in L_tasks[layer]:
                    layer += 1

                tmp1[o, d] = sharedMemory['L_tasks'][layer-1][olocal, dlocal]

                sharedMemory['L_done'] = tmp1  # with the insertkey

                L_tasks[originallayer][olocal, dlocal] = L_tasks[layer-1][olocal, dlocal]
                del L_tasks[layer-1][olocal, dlocal]

                # recalculate all necesseray variables in the shared memory L, C, cost
                # num_cities is a constant number!
                L, L_tasks, L_tasks_modified, C, C_task, C_fictive, T, flight_time_matrix, cost = \
                                gen_data.update_airfraight_inst(L_tasks, sharedMemory['fleet'], timestep, num_cities, sharedMemory['flighttimematrix'])

                print('Updating shared memory...')
                sharedMemory['L'] = L
                sharedMemory['L_tasks'] = L_tasks
                sharedMemory['L_tasks_modified'] = L_tasks_modified
                sharedMemory['C'] = C
                sharedMemory['C_fictive'] = C_fictive
                sharedMemory['C_task'] = C_task
                sharedMemory['timeinterval'] = T
                sharedMemory['num_citites'] = num_cities
                sharedMemory['costgraph'] = cost
                sharedMemory['flighttimematrix'] = flight_time_matrix

                print("++++++++++++++++++++++++++++++++++++++++++++++\n"
                      "Flight %3s is going from %3s to %3s at time %5s.\n"
                      "--------->Tons transported  %5s \n"
                      "++++++++++++++++++++++++++++++++++++++++++++++" %
                      (f, o, d, timestep, sharedMemory['L_done'][o, d][1]))

            else:

                print("++++++++++++++++++++++++++++++++++++++++++++++\n"
                      "Flight %3s is going from %3s to %3s at time %5s.\n"
                      "--------->Tons transported  %5s \n"
                      "++++++++++++++++++++++++++++++++++++++++++++++" %
                      (f, o, d, timestep, 0))

def run_schedule(sharedMemory):
    # during every timestep we must check if a new task has been
    # injected if it was, lock this proces until the optimization
    # gives a new
    for timestep in sharedMemory['timeinterval']:
        # now do this every second
        time.sleep(1)
        do_timestep(sharedMemory, timestep)
        print('#####################-END OF TIMESTEP: %4s-#####################' % timestep)

# then there is the simulation process. What it does is, it only reads from the shared
# memory and acts accordingly. So if after waiting for one second it does find
# the optimize boolean to be true, it calculates a new schedule on the according
# tasks
def simulation(sharedMemory):

    # next we are actually running the simmulation. So for every five
    # seconds we increment the timestep variable in the shared memory
    # by 0.5 ... yes ... that is what we are doing
    while True:
        time.sleep(1)
        # optimisation can only run when simulation has started
        if sharedMemory['simulate']:

            # test all timesteps
            # increment time
            sharedMemory['timestep'] += 0.5
            do_timestep(sharedMemory, sharedMemory['timestep'])



            print('simulation |--> proceed with timestep...')
            print('           |--> current time : %5s' % sharedMemory['timestep'])
            if sharedMemory['optimise']:
                print('optimising..')
                solve_optimisation_problem(sharedMemory)

            #check if we arrived at the last time
            if len(sharedMemory['timeinterval']) and sharedMemory['timeinterval'][-1] == sharedMemory['timestep']:
                print('simulation |--> +++++ Simulation finished +++++')
                sharedMemory['simulate'] = False
        else:
            print('simulation |--> pending...')
            print('           |--> current time : %5s' % sharedMemory['timestep'])


        if sharedMemory['optimise']:
            print('optimising..')
            solve_optimisation_problem(sharedMemory)
            time.sleep(5)
        print(sharedMemory)

        # termination signal
        if sharedMemory['terminate']:
            break

def run_fleet_loading_optimisation(sharedMem):

    L = sharedMem['L']
    L_tasks = sharedMem['L_tasks']
    L_tasks_modified = sharedMem['L_tasks_modified']
    C = sharedMem['C']
    C_fictive = sharedMem['C_fictive']
    F = sharedMem['fleet']
    T = sharedMem['timeinterval']
    cost = sharedMem['costgraph']
    ftm = sharedMem['flighttimematrix']
    num_cities = sharedMem['num_citites']
    timestep = sharedMem['timestep']
    schedule_x = sharedMem['schedule_x']
    schedule_y = sharedMem['schedule_y']
    loadingsystems = sharedMem['loadingsystems']
    LS_start = sharedMem['LS_start']

    model = af.transpt(L, L_tasks_modified, C, C_fictive, F, T, -1, -1, cost)
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
        C_full = [i for i in range(0, num_cities+1)]
        transp_time_ls = loading_gen_data.construct_airfraight_transp_loadingsystems(C_full, loading_C_task,
                                                                                     loading_C, ftm.flighttime)
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

if __name__ == '__main__':
    # threadsafe shared memeory manager
    manager = Manager()

    # this dictionary functions a an area where information
    #to the state of the multithread application is found.
    # This includes the information if a new Task has been
    # injected. So initially there is no task and the flights
    # get directed nowhere. Since we are working with a dictionary
    # coming out of the optimizer the simulation will need to get its
    # inforamtion from this dictionary datastructure. So a starter
    # would be to write a function that counts every second or so
    # and writes to the output console what flight was made. If
    # there is no flight, then there will be only the time output
    #--- > implementing....
    sharedDict = manager.dict()
    l = manager.list(range(10))
