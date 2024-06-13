import statistics
import numpy as np
class simulate_env:
    def __init__(self,worker_name:str,service_name:str,result_dir:str,
                 timeout_setting:float,t_max:int,w_perf:float,w_res:float):
        '''
        worker_name: the cluster name service locate
        service_name: indicate the service name
        IP: mn1 ip address
        IP1: mn2 ip address
        result_dir: the path to save the env recource data
        timeout_setting: indicate the request max reponse time 
        '''
        self.worker_name=worker_name
        self.service_name = service_name
        self.cpus = 1.0
        self.replica = 1
        self.cpu_utilization = 0.0
        self.scale=0
        # self.action_space = ['1', '1', '1']
        self.state = [self.replica, 0, self.cpus, 0] # replica / cpu utiliation / cpus / response time
        self.n_state = len(self.state)
        self.n_actions = 5 # None cpus +0.1 -0.1  replicas +1 -1 
        self.response_time_list=[]
        self.cpu_utilization_list=[]
        self.step_cpu_utilization = []
        self.step_rt = []
        # # two service url
        # self.url_list = ["http://" + IP + ":5000","http://" + IP1 + ":5500"]
        # self.url_list = [["http://" + IP + ":8000/replicas1","http://" + IP + ":8000/replicas2","http://" + IP + ":8000/replicas3"],
        #                  ["http://" + IP1 + ":8001/replicas1","http://" + IP1 + ":8001/replicas2","http://" + IP1 + ":8001/replicas3"]]
        # for caculate ideal cpu and response time 
        
        self.servetimemean=0
        self.servetimevariance=0
        # for calculate the reward
        self.result_dir=result_dir
        self.timeout_setting=timeout_setting
        self.t_max=t_max
        self.w_perf = w_perf
        self.w_res = w_res
    def reset(self,replicas:int,cpus:float):
        
        self.replica = replicas
        self.cpus = cpus
        self.state[0] = self.replica
        self.state[2] = self.cpus
    def action(self,idx):
        # None cpus +0.1 -0.1  replicas +1 -1 
        print ("scale the server resource")
        self.scale=0
        table=[0,0.1,-0.1,1,-1]
        if (idx==0) :return 
        if (idx<=2):
            temp=self.cpus+ table[int(idx)]
            if (temp>0.7 and temp<=1):
                self.cpus=round(temp, 2)
                return 
            return 
        else:
            temp=self.replica +table[int(idx)]
            if (temp>0 and temp<=3):
                self.replica=temp
                self.scale=1
                return 
            return 
    def save_cpu_usage(self,timestamp:int, inputRateTps):
        
        self.servetimemean=1/float(self.cpus*200)
        lambdaTps = inputRateTps/self.replica
        rho = lambdaTps * self.servetimemean
        if (rho*100>100) :rho=1.0
        path1 = self.result_dir + self.service_name + "_cpu.txt"
        f1 = open(path1, 'a')
        data1 = str(timestamp) + ' '+ str(rho*100)+ ' ' + str(self.replica)  + '\n'
        f1.write(data1)
        f1.close()
        return rho
        
    def save_reponse_time(self,timestamp:int, inputRateTps,rho):
        
        r=0.0
        if (rho >= 1.0) :
            r= self.timeout_setting
        else:
            lambdaTps = inputRateTps /float(self.replica)
            es2 = self.servetimevariance + self.servetimemean * self.servetimemean 
            r = self.servetimemean  + lambdaTps/2.0*es2/(1.0-rho)
        path1 = self.result_dir + self.service_name + "_response.txt"
        f1 = open(path1, 'a')
        data1 = str(timestamp) + ' '+ str(r) + ' ' + str(self.cpus) + ' ' + str(self.replica)+" " + str(inputRateTps)+'\n'
        f1.write(data1)
        f1.close()
        return r    
        
    def get_resource(self,timestamp,inputRateTps):
        rho=self.save_cpu_usage(timestamp,inputRateTps)
        rt=self.save_reponse_time(timestamp,inputRateTps,rho)
        self.cpu_utilization_list.append(rho*100)
        self.response_time_list.append(rt)

    def get_state(self):
        '''
        return the current state of enviornment, anf the reward from previous action
        ( because this environment need time to see the outcome), the reward function is a lot can be improve
        '''
        # calculate the response time mean, if one is timeout then all seem as timeout
        response_time_list=self.response_time_list[:]
        self.response_time_list=[]
        if self.timeout_setting not in response_time_list:
            mean_response_time = statistics.mean(response_time_list)
            mean_response_time = mean_response_time*1000  # 0.05s -> 50ms
        else:
            mean_response_time=self.timeout_setting*1000
        Rt = mean_response_time # get rt

        self.cpu_utilization = statistics.mean(self.cpu_utilization_list)
        self.cpu_utilization_list=[]
        # change the absolute percentage to relative percentage
        relative_cpu_utilization = self.cpu_utilization / 100 / self.cpus # get cpu usage
        relative_cpu_utilization = round( relative_cpu_utilization,8)
        Rt=round(Rt,8)
        

        # T_upper=self.timeout_setting*1000
        # B = np.log(1+0.5)/((T_upper-self.t_max)/self.t_max) # time constant
        # c_delay = np.where(Rt <= self.t_max, 0, np.exp(B * (Rt - self.t_max) / self.t_max) - 0.5)
        c_delay=0
        if(Rt>self.t_max): c_delay=1
        # cpu_utilization cost

        if relative_cpu_utilization >0.9:
            c_utilization = 1
        else:
            c_utilization = 0
        
        # calculate the reward
        # c_perf = max(c_delay, c_utilization)
        c_scale=self.scale
        c_perf = c_delay+ c_utilization
        
        # resource cost
        # c_res = (self.replica*self.cpus)/3   # replica*self.cpus / Kmax
        c_res=c_utilization<0.4
        next_state = []
        # # k, u, c # r

        # u = self.discretize_cpu_value(self.cpu_utilization)
        next_state.append(self.replica)
        next_state.append(relative_cpu_utilization)
        next_state.append(self.cpus)
        next_state.append(Rt)
        # next_state.append(request_num[timestamp])
        self.state = next_state
        # normalize
        # c_perf = 0 + ((c_perf - math.exp(-Tupper/t_max)) / (1 - math.exp(-Tupper/t_max))) * (1 - 0)  # min max normalize
        # c_res = 0 + ((c_res - (1 / 6)) / (1 - (1 / 6))) * (1 - 0)  # min max normalize
        reward_perf = self.w_perf * c_perf
        reward_res = self.w_res * c_res
        reward = -(reward_perf + reward_res)
        return next_state, reward, reward_perf, reward_res
