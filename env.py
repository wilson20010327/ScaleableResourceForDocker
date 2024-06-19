import requests,subprocess,json,time,statistics
import numpy as np
import utility.env_service as env_service
class env():
    def __init__(self,worker_name:str,service_name:str,IP:str,IP1:str,result_dir:str,
                 timeout_setting:int,t_max:int,w_perf:float,w_res:float,mp:bool=True):
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
        self.cpus = 1
        self.replica = 1
        self.cpu_utilization = 0.0
        self.action_space = ['1', '1', '1']
        self.state = [self.replica, 0, self.cpus, 0] # replica / cpu utiliation / cpus / response time
        self.n_state = len(self.state)
        self.n_actions = len(self.action_space)
        if not mp:
            self.n_actions = 5 # None cpus +0.1 -0.1  replicas +1 -1 
        self.response_time_list=[]
        self.step_cpu_utilization = []
        self.step_rt = []
        # # two service url
        # self.url_list = ["http://" + IP + ":5000","http://" + IP1 + ":5500"]
        self.url_list = [["http://" + IP + ":8000/replicas1","http://" + IP + ":8000/replicas2","http://" + IP + ":8000/replicas3"],
                         ["http://" + IP1 + ":8001/replicas1","http://" + IP1 + ":8001/replicas2","http://" + IP1 + ":8001/replicas3"]]
        self.result_dir=result_dir
        self.timeout_setting=timeout_setting
        self.t_max=t_max
        self.w_perf = w_perf
        self.w_res = w_res
        self.mp=mp
    def reset(self,replicas:int,cpus:float):
        '''
        reset the envorinment to the given setting, the env will first been sscaled to 0,
        after that scale to the given repilcas and set the cpus  
        '''
        self.replica = replicas
        self.cpus = cpus
        self.state[0] = self.replica
        self.state[2] = self.cpus
        print("reset envronment...")
        cmd_list = [
            "sudo docker-machine ssh default docker service update --replicas 0 "+self.service_name+"-1",
            "sudo docker-machine ssh default docker service update --replicas 0 "+self.service_name+"-2",
            "sudo docker-machine ssh default docker service update --replicas 0 "+self.service_name+"-3",
            "sudo docker-machine ssh default docker service update --replicas " + str(self.replica)+" " +self.service_name+"-1",
            "sudo docker-machine ssh default docker service update --limit-cpu " + str(cpus)+" "  + self.service_name+"-1",
            "sudo docker-machine ssh default docker service update --replicas " + str(self.replica) +" " +self.service_name+"-2",
            "sudo docker-machine ssh default docker service update --limit-cpu " + str(cpus)+" "  + self.service_name+"-2",
            "sudo docker-machine ssh default docker service update --replicas " + str(self.replica)+" "  +self.service_name+"-3",
            "sudo docker-machine ssh default docker service update --limit-cpu " + str(cpus) +" " + self.service_name+"-3",
        ]
        def execute_command(cmd):
            return subprocess.check_output(cmd, shell=True)
        for cmd in cmd_list:
            result = execute_command(cmd)
            print(cmd)
            # print(result)
        return self.state
    def action(self,replica,cpus=0):
        '''
        deal with the output of the model (replica,cpus), and save the action in the self parameter
        replica: scale repilas of the environment to the this number 
        cpus: set cpus of the environment to the this number
        '''
        # if action != '0':
        if self.mp:#mpdqn
            action_replica = int(replica)#action[0]
            action_cpus = float(cpus)#action[1][action_replica][0]#action[1]
            self.replica = action_replica + 1  # 0 1 2 (index)-> 1 2 3 (replica)
            self.cpus = round(action_cpus, 2)
            # scale, But for docker stable 3 containers have aready built, all we need to do is send to different proxy port 
            cmd2 = "sudo docker-machine ssh default docker service update --limit-cpu " + str(self.cpus) + " " + self.service_name
            for i in range(self.replica):
                print(self.service_name+"-"+str(i+1)+' cpu')
                returned_text = subprocess.check_output(cmd2+"-"+str(i+1), shell=True)
                
            
            time.sleep(1)  # wait service start
        else:#dqn
            idx=replica
            table=[0,0.1,-0.1,1,-1]
            if (idx==0) : 
                pass
            if (idx<=2):
                temp=self.cpus+ table[int(idx)]
                if (temp>0.7 and temp<=1):
                    self.cpus=round(temp, 2)
                    cmd2 = "sudo docker-machine ssh default docker service update --limit-cpu " + str(self.cpus) + " " + self.service_name
                    
                    for i in range(self.replica):
                        print(self.service_name+"-"+str(i+1)+' cpu')
                        returned_text = subprocess.check_output(cmd2+"-"+str(i+1), shell=True) 
            else:
                temp=self.replica +table[int(idx)]
                if (temp>0 and temp<=3):
                    self.replica=temp 
        print (self.service_name+" scale the server resource")
        print(self.service_name+' replica= '+str(self.replica)+' cpus= '+str(self.cpus))
    def save_cpu_usage(self,timestamp:int):
        '''
        Save the container's cpu usage data from docker stats to disk, 
        it has a drawback, the resolution (2 seconds) of the docker stats 
        makes this function works pretty slow.  
        '''
        cmd = "sudo docker-machine ssh " + self.worker_name + " docker stats --no-stream --format \\\"{{ json . }}\\\" "
        returned_text = subprocess.check_output(cmd, shell=True)
        my_data = returned_text.decode('utf8')
        # print(my_data.find("CPUPerc"))
        my_data = my_data.split("}")
        # state_u = []
        for i in range(len(my_data) - 1):
            # print(my_data[i]+"}")
            my_json = json.loads(my_data[i] + "}")
            name = my_json['Name'].split(".")[0]
            cpu = my_json['CPUPerc'].split("%")[0]
            if "app_mn" in name and float(cpu) > 0:
                path = self.result_dir + name + "_cpu.txt"
                f = open(path, 'a')
                data = str(timestamp) + ' '
                data = data + str(cpu) + ' ' + '\n'

                f.write(data)
                f.close()
        # print ("cpu usage") 
    def save_reponse_time(self,timestamp:int):
        '''
        Save the container's response time data to disk, 
        we use the simple request to tick the server and get the response time  
        '''
        path1 = self.result_dir + self.service_name + "_response.txt"
        f1 = open(path1, 'a')
        
        # URL
        service_name_list = ["app_mn1", "app_mn2"]
        url = self.url_list[service_name_list.index(self.service_name)][self.replica-1]
        try:
            response,response_time=env_service.get_respond_time(url,self.timeout_setting)
            # print(self.replica)
        except requests.exceptions.Timeout:
            response = "timeout"
            response_time = self.timeout_setting
        response_time=round(response_time,2)
        data1 = str(timestamp) + ' ' + str(response) + ' ' + str(response_time) + ' ' + str(self.cpus) + ' ' + str(self.replica) + '\n'
        f1.write(data1)
        f1.close()
        if str(response) != '200':
            response_time = self.timeout_setting
        # print ("response time")  
        self.response_time_list.append(response_time)
        return response_time
    def get_cpu_utilization_from_data(self):
        '''
        Get the last five env cpu usages dataset from disk, 
        and this function will check self.replica to import matching files
        '''
        path:list= [self.result_dir + self.service_name + '-1_cpu.txt',
                    self.result_dir + self.service_name + '-2_cpu.txt',
                    self.result_dir + self.service_name + '-3_cpu.txt']
        try:
            last_avg_cpu=[]
            for i in range(self.replica):
                print(path[i])
                f = open(path[i], "r")
                cpu = []
                time = []
                for line in f:
                    s = line.split(' ')
                    time.append(float(s[0]))
                    cpu.append(float(s[1]))
                # Get last five data
                last_avg_cpu.append(statistics.mean(cpu[-5:])) 
                f.close()
        except:
            print('cant open')
        last_avg_cpu=statistics.mean(last_avg_cpu)
        return last_avg_cpu
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

        self.cpu_utilization = self.get_cpu_utilization_from_data()
        # change the absolute percentage to relative percentage
        relative_cpu_utilization = self.cpu_utilization / 100 / self.cpus # get cpu usage
        
        
        # use moving average to smooth the value
        self.step_cpu_utilization.append(relative_cpu_utilization)
        self.step_rt.append(Rt)
        if len(self.step_cpu_utilization) == 4:
            relative_cpu_utilization = statistics.mean(self.step_cpu_utilization)
            Rt = statistics.mean(self.step_rt)
            self.step_cpu_utilization.pop(0)
            self.step_rt.pop(0)
        
        c_delay=0
        if(Rt>=self.t_max): c_delay=1
        # cpu_utilization cost

        if relative_cpu_utilization >0.9:
            c_utilization = 1
        else:
            c_utilization = 0
        
        # calculate the reward
        # c_perf = max(c_delay, c_utilization)
        
        c_perf = c_delay+ c_utilization
        
        # resource cost
        # c_res = (self.replica*self.cpus)/3   # replica*self.cpus / Kmax
        c_res=c_utilization<0.4
        # cpu_utilization cost

        # if relative_cpu_utilization > 0.8:
        #     x1 = 0.8 # the max cpu usage we want it learn
        #     x2 = 1.0 # the max cpu it can use
        #     y1 = self.t_max
        #     y2 = T_upper

        #     clip_relative_cpu_utilization = min(relative_cpu_utilization, 1)
        #     map_utilization = (clip_relative_cpu_utilization - x1) * ((y2 - y1) / (x2 - x1)) + self.t_max
        #     c_utilization = np.exp(B * (map_utilization - self.t_max) / self.t_max) - 0.5
        # else:
        #     c_utilization = 0
        
        # calculate the reward
        # c_perf = max(c_delay, c_utilization)
        # c_perf = c_delay+ c_utilization

        # resource cost
        # c_res = (self.replica*self.cpus)/3   # replica*self.cpus / Kmax
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


