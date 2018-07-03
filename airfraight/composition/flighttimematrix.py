import numpy as np


class FlightTimeMatrix():
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self):

        self.flighttime = 0
        self.flighttime_case = 0


    def construct_matrix_flighttime(self, n):
        flighttime = np.zeros((n + 1, n + 1))

        for i in range(n + 1):
            for j in range(i + 1, n + 1):
                flighttime[i, j] = np.random.randint(low=1, high=10, size=1)[0]
                flighttime[j, i] = flighttime[i, j]

        self.flighttime = flighttime

