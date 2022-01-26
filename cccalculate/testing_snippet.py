"""
[summary]
Testing date count and overlap merge
[description]
Taking date ranges determine which range over laps 
record and count them. This is just research code
"""
from datetime import datetime,timedelta

resourcing = 84
test_data = [
{'change_grp_id':1,'start_date':datetime(2019,9,1),'end_date':datetime(2019,10,3),'resources':2},
{'change_grp_id':2,'start_date':datetime(2019,8,1),'end_date':datetime(2019,10,3),'resources':5},
{'change_grp_id':3,'start_date':datetime(2019,9,11),'end_date':datetime(2019,9,13),'resources':1},
{'change_grp_id':4,'start_date':datetime(2019,11,1),'end_date':datetime(2019,11,8),'resources':1},
{'change_grp_id':5,'start_date':datetime(2019,9,5),'end_date':datetime(2019,9,7),'resources':3},
{'change_grp_id':6,'start_date':datetime(2019,9,5),'end_date':datetime(2019,9,8),'resources':3}]


sortedlist = sorted(intervals, key=lambda k: (k[0],k[1]))

def dmerge(inplist=sortedlist):
    for itm in inplist:
        print(itm)
    print('Working')

from ailist import AIList
import numpy as np
interval = [(1,105,3,205),(1,13,2,100),(1,15,1,35),(0,1,2,10),(4,13,10,21)]
sortedlist = sorted(intervals, key=lambda k: (k[0],k[1]))

starts = np.array([j[0] for i,j in enumerate(sortedlist)])
ends = np.array([j[1] for i,j in enumerate(sortedlist)])
ids = np.array([j[3] for i,j in enumerate(sortedlist)])
values = np.array([float(j[2]) for i,j in enumerate(sortedlist)])

i = AIList()
i.from_array(starts, ends, ids, values)


def parse_intervals(interval):
    # Inspect interval
    if not type(interval) is list:
        raise ValueError('List is required')
    else:
        if not all(type(itm) is tuple for itm in interval):
            raise ValueError('List must contain tuples of length 4')
        elif not all(len(itm) == 4 for itm in interval):
            raise ValueError('Tuples must be of length 4')

    # Sort intervals - not strictly necessary but makes it easier to read
    sortedlist = sorted(interval, key=lambda k: (k[0],k[1]))

    # Enter array details
    # One added to starts and ends to move anything off zeros
    # It will be removed once intervals are calculated
    starts = np.array([j[0]+1 for i,j in enumerate(sortedlist)])
    ends = np.array([j[1]+1 for i,j in enumerate(sortedlist)])
    ids = np.array([j[3] for i,j in enumerate(sortedlist)])
    values = np.array([float(j[2]) for i,j in enumerate(sortedlist)])

    # Create interval tree
    i = AIList()
    i.from_array(starts, ends, ids, values)

    # Iterate through each interval
    int_dict = {}
    for itm in sortedinterval:
        int_list = []
        for vals in range(itm[0],itm[1]):
            check_array = i.intersect_index(itm[0],vals)




# Now iterate through the days until 


intervals = [(1,105,3,205),(1,13,2,100),(1,15,1,35),(0,14,2,10),(4,13,10,21)]
sortedlist = sorted(intervals, key=lambda k: (k[0],k[1]))
i = AIList()
for itm in sortedlist:
    i.add(itm[0],itm[1],itm[3])


from ailist import AIList
import numpy as np
i = AIList()
starts = np.arange(10,1000,100)
ends = starts + 50
ids = starts
values = np.ones(10)
i.from_array(starts, ends, ids, values)
i.display()


# starts = np.array([1,1,1,0,4])
# ends = np.array([105,13,15,14,13])
# ids = np.array([205,100,35,10,21])
# values = np.array([3,2,1,2,10])
# j = AIList()
# j.from_array(starts,ends,ids,values)


# 1 = 0-1 for 1 resource
# 1 = 1-4 for 5 resource
# 1 = 4-13 for 5 resource
# 1 = 13-14 for 4 resource 
sorted_intervals = sorted(intervals, key=lambda k: (k[0],k[1]))

data_dict = {}
total_resource = 18
intervals = []
for itm in range(0,len(sorted_intervals)):
    data_list = [] 
    is_first = true
    interval_start = [0,0]
    interval_middle = [0,0]
    interval_end = [0,0]

    for itms in [val for key, val in enumerate(sorted_intervals) if key not in [itm]]:
        # 0,14 sorted_intervals[itm][0]

        interval_start = [0,0]
        calculate_interval = itms[0] - sorted_intervals[itm][0]

        if is_first = true:
            data_list[0] = sorted_intervals[itm][0]
        else:
            data_list[0] = 



        is_first = false





