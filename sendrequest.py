import utility.locustWorkloadCreator as locustWorkloadCreator
class workloadcreater:
    def __init__(self,requestResultFolderPath:str) :
        self.active:bool=False
        self.requestResultFolderPath=requestResultFolderPath
        pass
    def start(self,url:str,request_detail:dict,
              replica:int, timestamp:int,episode:int,):
        self.active=True
        filename=self.requestResultFolderPath+str(episode)+"_"+str(timestamp)+".html"
        data_rate=request_detail['data_rate'][timestamp]
        print("request start  "+ str(data_rate))
        locustWorkloadCreator.startTask(url,data_rate,data_rate,replica,filename)
        
        return     
    def stop(self):
        if not self.active:
            return 
        print("clean request")
        locustWorkloadCreator.cleanTask()
        self.active = False
        
        return 