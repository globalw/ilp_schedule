from pyscipopt import Model, quicksum
import numpy as np

def transp_loadingsystems(loadingsystems, flight_variables, L_tasks, T, C, transp_time_ls, LS_start, cost):
    """ transp_loadingsystems is solving the loading system problem based on flight_variables which are
        found in the optimisation problem of the flight assignement problem before

        parameters:
        flighttime          -   nxn matrix ((o,d) entry gives the flight time from o to d)
        loadingsystems      -   dict((i):[w]) (w = max lifting weight)
        flight_variables    -   [[f,o,d,t], ...] (aircraft f flies from o to d at departure time t)
        L_task              -   [{(o,d):[td,w,f_time],...},...] (as in optimisation of flight assignment problem)
        T                   -   time interval
        C                   -   set of the cities
        transp_time_ls      -   nxn matrix ((o,d) entry gives the transport time of the loading system form o to d)
        LS_start            -   dict{(l):c} (loading system l is in c at time -0.5)
        cost                -   dict{(l,o,d,t): value, ...} (cost of transport of loadong system from o to d at time t)
    """
    print('build optimisation problem...')
    model = Model("loading systems")

    # precision
    EPS = 1.e-6

    T_mod = np.arange(-0.5, T[-1]+1, 1)
#  ---------------------------------------------------------------------------------------------------------
# Variables
    # Create variables a_lodt and b_lot
    a,b = {},{}

    print('building variables...')
    # decision variable a=1 if loading system l is transported from o to d with departure time t; a=0 else
    for l in loadingsystems:
        for o in C:
            for d in C:
                for t in T:
                    if o != d:
                        a[l, o, d, t] = model.addVar(vtype="B", name="a(%s, %s, %s, %s)" % (l, o, d, t))

    # ground arch variables (number of air crafts at location o at time t)
    for l in loadingsystems:
        for o in C:
            for t in T_mod:
                b[l, o, t] = model.addVar(vtype="B", name="b(%s, %s, %s)" % (l, o, t))


# ---------------------------------------------------------------------------------------------------------
# Constraints

    # (1) continuity between transport and ground arches of loading systems
    for l in loadingsystems:
        for t in T:
            for o in C:
                    outgo_flight = quicksum(a[l, o, d, t] for d in C if (o, d) in transp_time_ls)
                    income_flight = quicksum(a[l, d, o, t-transp_time_ls[d, o]] for d in C if (d, o) in transp_time_ls if t-transp_time_ls[d, o] >= 0)
                    model.addCons(b[l, o, t-0.5] + income_flight - outgo_flight - b[l, o, t+0.5] == 0)

    # (2) starting points for loading systems
    for l in loadingsystems:
        for o in C:
            if o == LS_start[l]:
                model.addCons(b[l, LS_start[l], T_mod[0]] == 1)
            else:
                model.addCons(b[l, o, T_mod[0]] == 0)

    # (3) lifting weight of loading system exceeds the weight of commodity
    for k, v in L_tasks.items():
        for x in flight_variables:
            if (x[1] == k[0] and x[2] == k[1]):
                model.addCons(quicksum(b[l, x[1], x[3]-0.5] for l in loadingsystems if loadingsystems[l] >= v[1]) == 1)
                model.addCons(quicksum(b[l, x[2], x[3]+v[2]-0.5] for l in loadingsystems if loadingsystems[l] >= v[1]) == 1)

# ---------------------------------------------------------------------------------------------------------
    # Objective
    model.setObjective(quicksum(cost[l, o, d, t]*a[l, o, d, t] for l in loadingsystems for o in C for d in C for t in T if (l, o, d, t) in cost), "minimize")

    print('solve optimisation problem...')
    model.optimize()

    model.data = a, b
    return model

# ---------------------------------------------------------------------------------------------------------

