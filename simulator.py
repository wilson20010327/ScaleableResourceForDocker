class simulate_env:
    def __init__(self,worker_name:str,service_name:str,result_dir:str,
                 timeout_setting:int,t_max:int,w_perf:float,w_res:float):
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
        self.step_cpu_utilization = []
        self.step_rt = []
        # # two service url
        # self.url_list = ["http://" + IP + ":5000","http://" + IP1 + ":5500"]
        # self.url_list = [["http://" + IP + ":8000/replicas1","http://" + IP + ":8000/replicas2","http://" + IP + ":8000/replicas3"],
        #                  ["http://" + IP1 + ":8001/replicas1","http://" + IP1 + ":8001/replicas2","http://" + IP1 + ":8001/replicas3"]]
        self.result_dir=result_dir
        self.timeout_setting=timeout_setting
        self.t_max=t_max
        self.w_perf = w_perf
        self.w_res = w_res
    def reset(self,replicas:int,cpus:float):
        '''
        reset the envorinment to the given setting, the env will first been sscaled to 0,
        after that scale to the given repilcas and set the cpus  
        '''
        self.replica = replicas
        self.cpus = cpus
        self.state[0] = self.replica
        self.state[2] = self.cpus
    def action(self,replica,cpus):
        '''
        deal with the output of the model (replica,cpus), and save the action in the self parameter
        replica: scale repilas of the environment to the this number 
        cpus: set cpus of the environment to the this number
        '''
        # if action != '0':
        action_replica = int(replica)#action[0]
        action_cpus = float(cpus)#action[1][action_replica][0]#action[1]
        self.replica = action_replica + 1  # 0 1 2 (index)-> 1 2 3 (replica)
        self.cpus = round(action_cpus, 2)

        print ("scale the server resource")
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

        data1 = str(timestamp) + ' ' + str(response) + ' ' + str(response_time) + ' ' + str(self.cpus) + ' ' + str(self.replica) + '\n'
        f1.write(data1)
        f1.close()
        if str(response) != '200':
            response_time = self.timeout_setting
        # print ("response time")  
        return response_time