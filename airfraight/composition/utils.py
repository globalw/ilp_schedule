from pyscipopt import Model, quicksum
import numpy as np

def transpt(L, L_tasks_mod, C, C_fictive, F, T, x_start, y_start, num_cities):
    """transp -- model for solving the transportation problem
    Parameters:
        L               - dict of tasks with modified city numbers according to the layers and fictive flights,
                          fighttime appended: {(o,d):[td, w, f_time]}
        L_tasks_mod     - dict of tasks with modified city numbers according to the layers,
                          fighttime appended: {(o,d):[td, w, f_time]}
        C               - list of  all cities over all layers plus fictive cities
        C_fictive       - list of fictive cities
        F               - dict of fleet {f:[w_max, tank_max]}
        T               - set of discretized times
        x_start         - dict of initial flights
        y_start         - dict of initial ground postions
    Returns a model, ready to be solved.
    """
    print('build optimisation problem...')
    model = Model("airfraight")

    # precision
    EPS = 1.e-6

    # T_mod for ground arc variables
    T_mod = np.arange(-0.5, T[-1]+1, 1)

#  ---------------------------------------------------------------------------------------------------------
# Variables
    # Create variables x_fodt and y_ot
    x, y, z = {}, {}, {}

    print('building variables...')
    # decision variable x=1 if f flies from o to d with departure time t; x=0 else
    for f in F:
        for t in T:
            for o in C:
                for d in C:
                    if o != d:
                        x[f, o, d, t] = model.addVar(vtype="B", name="x(%s, %s, %s, %s)" % (f, o, d, t))


    # ground arc variables (y=1 if aircraft f at location o at time t)
    for f in F:
        for t in T_mod:
            for o in C:
                y[f, o, t] = model.addVar(vtype="B", name="y(%s, %s, %s)" % (f, o, t))

    # variable for tank at time t for an airplane f
    for f in F:
        for t in T:
             z[f, t] = model.addVar(vtype="C", name="z(%s, %s)" % (f, t))

# ---------------------------------------------------------------------------------------------------------
# Constraints

    # (1) every task is flown exactly once
    for o in C:
        for d in C:
            if (o, d) in L_tasks_mod:
                model.addCons(quicksum(x[f, o, d, t] for f in F for t in T) == 1)



    # (2) continuity between flights and ground arches (very old version -> understand the calculation and does not work)
    for f in F:
        for t in T:
            for o in C:
                outgo_flight = quicksum(x[f, o, d, t] for d in C if (o, d) in L)
                income_flight = quicksum(x[f, d, o, t-L[d, o][2]] for d in C if (d, o) in L.keys() if t-L[d, o][2] >= 0)
                model.addCons(y[f, o, t-0.5] + income_flight - outgo_flight - y[f, o, t+0.5] == 0)


    # (3) assign the location of each aircraft in the beginning of optimisation
    if x_start != -1 and y_start != -1:
        # (3a) starting points for aircraft postition
        for k in y_start:
            model.addCons(y[k] == y_start[k])

        # (3b) starting points for aircraft starting times at position to position
        for k in x_start:
            model.addCons(x[k] == x_start[k])
    else:
        # (3c) starting from the base
        for f in F:
            model.addCons(y[f, C[0], T_mod[0]] == 1)
            C_mod = C[1:]
            for c in C_mod:
                model.addCons(y[f, c, T_mod[0]] == 0)


    # (6) no exceed of the capacity of the aircraft allowed
    for f in F:
        for t in T:
            for k, v in L_tasks_mod.items():
                model.addCons(F[f][0] - v[1]*x[f, k[0], k[1], t] >= 0)


    # (7) no exceed of the deadline of the task
    for f in F:
        for t in T:
            for k, v in L_tasks_mod.items():
                model.addCons(x[f, k[0], k[1], t]*t + v[2] <= v[0])

    # (8) full tank at time 0
    for f in F:
        model.addCons(z[f, 0] == F[f][1])

    # (9) refill at base (C[0])
    for f in F:
        for t in T:
            if t >= 1:


                C_without_base = []
                for c in C_fictive:
                    if t-L[c, C[0]][2] >= 0:
                        C_without_base.append(c)

                C2_without_base = []
                for o in C:
                    for d in C:
                        if (o, d) in L:
                            if d != C[0] and t-L[o, d][2] >= 0:

                                C2_without_base.append([o, d])

                base_at_t = quicksum(x[f, o, C[0], t-L[o,  C[0]][2]] for o in C_without_base)
                tank_loss = quicksum((L[c[0], c[1]][2]) * x[f, c[0], c[1], t-L[c[0], c[1]][2]] for c in C2_without_base)
                # the "fuel" you have now, is the sum of all "fuel"-loss subtracted from the tank and filled by every
                # pass of the base
                model.addCons(z[f, t] == z[f, t - 1] - tank_loss + (-z[f, t - 1] + F[f][1]) * base_at_t)
                # at every time we need enough "fuel" in order to get back
                model.addCons(z[f, t] >= 0)

# ---------------------------------------------------------------------------------------------------------

    # calculate cost dict{(f,o,d,t)}
    cost = dict()
    for f in range(len(F)):
        for t in T:
            for k, v in L.items():
                if (k[0] % num_cities) == (k[1] % num_cities):
                    cost[f, k[0], k[1], t] = 0.01/len(L_tasks_mod)
                else:
                    cost[f, k[0], k[1], t] = (F[f][0] - v[1]) * v[2]

    # Objective
    model.setObjective(quicksum(cost[f, o, d, t]*x[f, o, d, t] for f in F for o in C for d in C for t in T if (f, o, d, t) in cost), "minimize")

    print('solve optimisation problem...')
    model.optimize()

    model.data = x, y, z
    return model

# ---------------------------------------------------------------------------------------------------------
def write_opt_res_to_values(model):

    EPS = 1.e-6
    x, y, z = model.data

    x_val = dict()
    y_val = dict()
    z_val = dict()
    # ignore all zeros
    for j in x:
        if model.getVal(x[j]) > EPS:
            x_val[j] = model.getVal(x[j])

    for j in y:
        if model.getVal(y[j]) > EPS:
            y_val[j] = model.getVal(y[j])
    for j in z:
        if model.getVal(z[j]) > EPS:
            z_val[j] = model.getVal(z[j])

    return x_val, y_val, z_val