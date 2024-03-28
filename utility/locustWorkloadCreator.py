import subprocess,time,signal,os

taskSet=[]

def startTask(serverIp:str,userNum:int,spawnRate:int,mode=1,resultFilePath=None):
    '''
    Create the users to connect to the target server, the task is define in locustTest.py file
    taskSet: to store the task which we create
    serverIp: the tareget server ip 
    userNum: the users amount that we want to create
    spawnRate: the time limit for create the target amount of users
    mode: correspond to replica, because the disadvantage of the docker swarm (unstable when using replica by default), need to create the proxy by myself 
    resultFilePath: the request stasticts result saving place
    '''
    if(resultFilePath==None):
        locustTaskPath='./locustTest1.py'
        taskSet.append(subprocess.Popen(
            ['locust','-f',locustTaskPath]))
    else:
        if(mode==1): locustTaskPath='./utility/locustTest1.py'
        if(mode==2): locustTaskPath='./utility/locustTest2.py'
        if(mode==3): locustTaskPath='./utility/locustTest3.py'
        print(":::"+str(serverIp)+" "+str(mode))
        taskSet.append(subprocess.Popen(
            ['locust','-f',locustTaskPath,'-H',serverIp,'--headless','-u',str(userNum),'-r',str(spawnRate),'--html',resultFilePath], stderr=subprocess.DEVNULL))


def cleanTask():
    '''
    clean the taskset which contain tasks we created before
    '''
    for i in taskSet:
        print(i.poll())
        if(i.poll()==None):
            # os.killpg(os.getpgid(i.pid),signal.SIGTERM)
            i.send_signal(signal.SIGINT)
            # i.send_signal(signal.SIGTERM)
            try:
                i.wait(5)
            except:
                print("cannot")
                i.send_signal(signal.SIGTERM)
                i.wait(5)
            # if(i.poll()==None):i.send_signal(signal.SIGTERM)
        print(i.poll())
    taskSet.clear()



if __name__=='__main__':
    # locustTaskPath='./locustTest.py'
    serverIp="http://192.168.99.102:8000/replicas2"
    filename='./'+'try'+".html"
    print(filename,serverIp)
    try:
        startTask(serverIp,5,5,2,filename)
        # startTask(serverIp,5,5)
        while(True):
            pass
    except:
        cleanTask()
    