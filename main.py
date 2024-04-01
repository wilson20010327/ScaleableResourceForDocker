from setting import *

if __name__ =='__main__':
    workload=workloadcreater(requestResultFolderPath)
    mn1=env('worker','app_mn1',IP,IP1,result_dir,timeout_setting,Tmax_mn1,w_perf,w_res)
    mn2=env('worker1','app_mn2',IP,IP1,result_dir,timeout_setting,Tmax_mn2,w_perf,w_res)
    agent_mn1=agent(result_dir,'app_mn1',mn1.n_state,mn1.n_actions,test)
    agent_mn2=agent(result_dir,'app_mn2',mn2.n_state,mn2.n_actions,test)
    agent_mn1.set_model(epsilon_initial,batch_size,gamma
                        ,initial_memory_threshold,replay_memory_size,epsilon_steps
                        ,tau_actor,tau_actor_param,use_ornstein_noise
                        ,learning_rate_actor,learning_rate_actor_param,epsilon_final
                        ,clip_grad,layers,multipass
                        ,action_input_layer,seed
                        )
    agent_mn2.set_model(epsilon_initial,batch_size,gamma
                        ,initial_memory_threshold,replay_memory_size,epsilon_steps
                        ,tau_actor,tau_actor_param,use_ornstein_noise
                        ,learning_rate_actor,learning_rate_actor_param,epsilon_final
                        ,clip_grad,layers,multipass
                        ,action_input_layer,seed
                        )
    step=0
    for epoch in range (epochs):
        # reset env
        mn1.reset(ini_replica1,ini_cpus1)
        mn2.reset(ini_replica2,ini_cpus2)
        # make the scaling process pipline to increate the efficiency 
        mn1reset=threading.Thread(target=mn1.reset,args=(ini_replica1,ini_cpus1,))
        mn2reset=threading.Thread(target=mn2.reset,args=(ini_replica2,ini_cpus2,))
        mn1reset.start()
        mn2reset.start()
        mn1reset.join()
        mn2reset.join()
        # init model
        
        # start workload
        url = "http://" + IP + ":8000/replicas" +str(mn1.replica)
        workload.start(url,request_detail,mn2.replica,0,epoch)
        response_time_list_1=[]
        response_time_list_2=[]
        done = False
        for timestamp in range(1,real_run+1):
            print('timestamp: ', timestamp)
            if timestamp % menitor_period ==0 :
                # stop workload
                workload.stop()
                
                if timestamp == (real_run):
                    done = True
                # get state info by disk, remember to stop for docker stats delay(about 2second) 
                cpu_mn1.join()
                cpu_mn2.join()


                # get state
                next_state_1, reward_1, reward_perf_1, reward_res_1 =mn1.get_state(response_time_list_1)
                response_time_list_1=[]
                # Covert np.float32
                next_state_1 = np.array(next_state_1, dtype=np.float32)
                next_state_2, reward_2, reward_perf_2, reward_res_2 =mn2.get_state(response_time_list_2)
                response_time_list_2=[]
                # Covert np.float32
                next_state_2 = np.array(next_state_2, dtype=np.float32)

                # model update
                if int(timestamp/menitor_period)>1:
                    agent_mn1.print_step(step,next_state_1,reward_1,reward_perf_1,reward_res_1,done)
                    agent_mn2.print_step(step,next_state_2,reward_2,reward_perf_2,reward_res_2,done)
                    if not test:
                        agent_mn1.step(next_state_1,reward_1,done)
                        agent_mn1.model.epsilon_decay()
                        agent_mn2.step(next_state_2,reward_2,done)
                        agent_mn2.model.epsilon_decay()

                
               
                if (not done):
                    # create action according new state 
                    act1_replicas,act1_cpus=agent_mn1.act(next_state_1)
                    act2_replicas,act2_cpus=agent_mn2.act(next_state_2)
                    # env action
                    # mn1.action(action_1)
                    # mn2.action(action_2)
                    # scaling part of the dokcer so slow use thread to improve the scaling time
                    mn1action=threading.Thread(target=mn1.action,args=(act1_replicas,act1_cpus,))
                    mn2action=threading.Thread(target=mn2.action,args=(act2_replicas,act2_cpus,))
                    mn1action.start()
                    mn2action.start()
                    # assign state value to previous state value
                    mn1action.join()
                    mn2action.join()
                    agent_mn1.next()
                    agent_mn2.next()
                    step+=1
                    # start workload
                    url = "http://" + IP + ":8000/replicas" +str(mn1.replica)
                    workload.start(url,request_detail,mn2.replica,timestamp,epoch)
               
            
            # get the cou usage from docker stats too slow need to use thread
            cpu_mn1=threading.Thread(target=mn1.save_cpu_usage,args=(timestamp,))
            cpu_mn1.start()
            cpu_mn2=threading.Thread(target=mn2.save_cpu_usage,args=(timestamp,))
            cpu_mn2.start()
            if timestamp % menitor_period >= menitor_period-5:
                # how to determine the amount of supervise response time
                # tick to server make env save response time
                response_time_list_1.append(mn1.save_reponse_time(timestamp))
                response_time_list_2.append(mn2.save_reponse_time(timestamp))
                
            # the timer tick 
            time.sleep(1)
    
    workload.stop()
    if (not test):
        agent_mn1.model.save_models(result_dir + agent_mn1.service_name + "_" + str(seed))
        agent_mn2.model.save_models(result_dir + agent_mn2.service_name + "_" + str(seed))
    print(datetime.datetime.now())