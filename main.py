from setting import *
request_plot=[]
if __name__ =='__main__':
    # workload=workloadcreater(requestResultFolderPath)
    mn1=simulate_env('worker','app_mn1',result_dir,timeout_setting,Tmax_mn1,w_perf,w_res)
    mn2=simulate_env('worker1','app_mn2',result_dir,timeout_setting,Tmax_mn2,w_perf,w_res)
    
    agent_mn1=Agent('app_mn1',mn1.n_state,mn1.n_actions,128,result_dir,not test)
    agent_mn2=Agent('app_mn2',mn2.n_state,mn2.n_actions,128,result_dir,not test)
    
    step=0
    
    for epoch in range (epochs):
        # reset env
        # make the scaling process pipline to increate the efficiency 
        mn1reset=threading.Thread(target=mn1.reset,args=(ini_replica1,ini_cpus1,))
        mn2reset=threading.Thread(target=mn2.reset,args=(ini_replica2,ini_cpus2,))
        mn1reset.start()
        mn2reset.start()
        mn1reset.join()
        mn2reset.join()
        # init model
        prev=0
        # start workload
        # url = "http://" + IP + ":8000/replicas" +str(mn1.replica)
        # workload.start(url,request_detail,mn2.replica,0,epoch)
        done = False
        for timestamp in range(1,real_run+1):
            print('timestamp: ', timestamp)
            if timestamp % menitor_period ==0 :
                if timestamp == (real_run):
                    done = True
                request_plot.append(request_num)
                if timestamp % (menitor_period*5)==0: 
                    prev=0
                
                # get state
                next_state_1, reward_1, reward_perf_1, reward_res_1 =mn1.get_state()
                next_state_2, reward_2, reward_perf_2, reward_res_2 =mn2.get_state()
                
                # Covert np.float32
                next_state_1 = np.array(next_state_1, dtype=np.float32)
                next_state_2 = np.array(next_state_2, dtype=np.float32)
                
                # model update
                if int(timestamp/menitor_period)>1:
                    agent_mn1.print_step(step,next_state_1,reward_1,reward_perf_1,reward_res_1,done)
                    agent_mn2.print_step(step,next_state_2,reward_2,reward_perf_2,reward_res_2,done)
                    if not test:
                        agent_mn1.step(next_state_1,reward_1,done)
                        agent_mn2.step(next_state_2,reward_2,done)

                
               
                if (not done):
                    # create action according to new state 
                    action1=agent_mn1.select_action(next_state_1)
                    action2=agent_mn2.select_action(next_state_2)
                    # env action
                    # mn1.action(action_1)
                    # mn2.action(action_2)
                    # scaling part of the dokcer so slow use thread to improve the scaling time
                    mn1action=threading.Thread(target=mn1.action,args=(action1,))
                    mn2action=threading.Thread(target=mn2.action,args=(action2,))
                    mn1action.start()
                    mn2action.start()
                    # wait until the scaling process done
                    mn1action.join()
                    mn2action.join()
                    # assign state value to previous state value
                    agent_mn1.next()
                    agent_mn2.next()
                    step+=1
                    
            # get the cpu usage from docker stats too slow need to use thread
            if timestamp % menitor_period >= menitor_period-5:
                
                request_num=request_detail['data_rate']
                
                if (request_detail['ifdynamic']):
                    def fluctuate_function_sin(prev,x, mean=data_rate, max_value=dymax, min_value=dymin,func_num=func_num):
                        x=int(x/5)
                        temp=0
                        temp=mean + (max_value - min_value) / 2 * math.sin(x)
                        # temp=min_value+(max_value - min_value)*x/24
                        if (prev==0):
                            
                            return temp
                        else:
                            return prev
                    prev=request_num=int(fluctuate_function_sin(prev,int(timestamp/30)))
                mn1.get_resource(timestamp,request_num)
                mn2.get_resource(timestamp,int(request_num*0.2))
                
            # the timer tick 
            # time.sleep(1)
    
    if (not test):
        agent_mn1.save_model(result_dir + agent_mn1.service_name + "_" + str(seed))
        agent_mn2.save_model(result_dir + agent_mn2.service_name + "_" + str(seed))
    print(datetime.datetime.now())

    x=[i for i in range(len(request_plot))]
    plt.plot(x, request_plot)
    plt.xlabel('time')
    plt.ylabel('request num')
    plt.savefig(result_dir+"request_plot.jpg")
    plt.show()