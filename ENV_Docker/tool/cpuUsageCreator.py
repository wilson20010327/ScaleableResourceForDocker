
import subprocess
import multiprocessing as mp
import threading
import time,signal,os
class StressCreator():
    def __init__(self) -> None:
        self.stress_string = 'stress-ng --cpu {0} --timeout {1}s -l {2}'
        self.num_cpu=0
        self.cpu_usage=0
        self.time_long=0
        self.cmd=None
        self.task=[]
        if self.num_cpu > mp.cpu_count():
            self.num_cpu = mp.cpu_count()
        threading.Thread.__init__(self)
        pass
    def stress_setting(self,num_cpu:int,time_long:int,cpu_usage:int):
        self.num_cpu=num_cpu
        self.cpu_usage=cpu_usage
        self.time_long=time_long
        if self.num_cpu > mp.cpu_count():
            self.num_cpu = mp.cpu_count()
    def get_setting(self):
        return self.num_cpu,self.time_long,self.cpu_usage  
    
    def create_job(self,cpu_num:int, time_long:int,cpu_usage:int):
        """
        :param cpu_num: number of cpus
        :param time_long: amount of time
        :param cpu_usage: percentage of the cpu been setted
        """
        self.stress_setting(cpu_num,time_long,cpu_usage)
        self.cmd = self.stress_string.format(cpu_num, time_long,cpu_usage)
    def run(self):
        if(self.cmd==None):
            raise ValueError('CMD hasn\'t setted before run') 
        # proc = subprocess.run( self.cmd, shell=True)   
        self.task.append(subprocess.Popen(["stress-ng", "--cpu", str(self.num_cpu), "--timeout",str(self.time_long)+'s',"-l",str(self.cpu_usage),'--taskset','0'] ))
    def stop(self):
        for i in self.task:
            print(i)
            i.terminate()
            i.wait()
            print(i.poll())
        pass

if __name__=="__main__":
    stressJob=StressCreator()
    stressJob.create_job(2,0,100)
    stressJob.run()
    time.sleep(10)
    stressJob.stop()
    print('??')
    
    print('??')