import os.path
import re


def read_flights(filename):

    num_cities=0
    L_tasks=[]
    num_layer = 0
    if not os.path.isfile(filename):
        print(filename, ": File does not exist.")

    with open(filename) as f:
        content=f.read().splitlines()
        f.close()

    for line in content:
        if (line[0]!="#"):
            data=re.findall('\d+', line)

            isin=0

            for i in range(num_layer):
                if (int(data[0]), int(data[1])) in L_tasks[i]:
                    isin=isin+1
            if isin==num_layer or len(L_tasks)==0:
                num_layer=num_layer+1
                L_tasks.append(dict())

            L_tasks[isin][int(data[0]), int(data[1])] =[int(data[2]), int(data[3]), int(data[4])]

            if max(int(data[0]), int(data[1])) > num_cities:
                num_cities=max(int(data[0]), int(data[1]))

    L_tasks.append({})
    return L_tasks, num_layer, num_cities



def read_fleet(filename):
    if not os.path.isfile(filename):
        print(filename, ": File does not exist.")

    with open(filename) as f:
        content=f.read().splitlines()
        f.close()
    count = 0
    F=dict()
    for line in content:


        if (line[0]!="#"):
            data=re.findall('\d+', line)
            F[count]=[int(data[0]), int(data[1]), int(data[2])]
            count=count+1

    return F

if __name__ == "__main__":
    L_tasks, num_layer =read_flights("example.flights")

    print(num_layer)

    for i in range(len(L_tasks)):
        for j in L_tasks[i]:
            print (L_tasks[i][j])