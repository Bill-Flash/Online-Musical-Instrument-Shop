import time
def produce_id():
    localtime = time.localtime(time.time())

    print("本地时间为 :", localtime)
    print(localtime.tm_year)
    id="#"+str(localtime.tm_year)
    if localtime.tm_mon<10:
        id=id+ "0"+str(localtime.tm_mon)
    else:
        id = id+str(localtime.tm_mon)
    if localtime.tm_mday<10:
        id = id + "0" + str(localtime.tm_mday)
    else:
        id = id + str(localtime.tm_mday)
    if localtime.tm_hour < 10:
        id = id + "0" + str(localtime.tm_hour)
    else:
        id = id + str(localtime.tm_hour)
    if localtime.tm_min < 10:
        id = id + "0" + str(localtime.tm_min)
    else:
        id = id + str(localtime.tm_min)
    print(id)
    return id

if __name__ == '__main__':
    produce_id()