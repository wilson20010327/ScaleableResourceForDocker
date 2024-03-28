from setting import *

if __name__ =='__main__':
    workload=workloadcreater(requestResultFolderPath)
    mn1=env('worker','app_mn1',IP,IP1,result_dir,timeout_setting,Tmax_mn1,w_perf,w_res)
    # mn2=env('worker1','app_mn2',IP,IP1,result_dir,timeout_setting)
    agent_mn1=agent(result_dir,'app_mn1',mn1.n_state,mn1.n_actions,test)
    agent_mn1.set_model(epsilon_initial,batch_size,gamma
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
        # init model
        # prepare first state
        # start workload
        url = "http://" + IP + ":8000/replicas" +str(mn1.replica)
        workload.start(url,request_detail,mn1.replica,0,epoch)
        response_time_list=[]
        done = False
        for timestamp in range(1,real_run+1):
            print('timestamp: ', timestamp)
            if timestamp % menitor_period ==0 :
                # stop workload
                workload.stop()
                
                if timestamp == (real_run):
                    done = True
                # get state info by disk, remember to stop for at least 2 second because dpcker stats delay 
                time.sleep(2)


                # get state
                next_state, reward, reward_perf, reward_res =mn1.get_state(response_time_list)
                response_time_list=[]
                # Covert np.float32
                next_state = np.array(next_state, dtype=np.float32)
                
                # model update
                if int(timestamp/menitor_period)>1:
                    agent_mn1.print_step(step,next_state,reward,reward_perf,reward_res,done)
                    if not test:
                        agent_mn1.step(next_state,reward,done)

                
               
                if (not done):
                    # create action by ne w state 
                    action=agent_mn1.act(next_state)
                    # env action
                    mn1.action(action)
                    # assign state value to previous state value
                    agent_mn1.next()
                    step+=1
                    # start workload
                    url = "http://" + IP + ":8000/replicas" +str(mn1.replica)
                    workload.start(url,request_detail,mn1.replica,timestamp,epoch)
               
            
            # get the cou usage from docker stats too slow need to use thread
            cpu_mn1=threading.Thread(target=mn1.save_cpu_usage,args=(timestamp,))
            cpu_mn1.start()
            if timestamp % menitor_period >= menitor_period-5:
                # how to determine the amount of supervise response time
                # tick to server make env save response time
                response_time_list.append(mn1.save_reponse_time(timestamp))
                
            # store resource message
            time.sleep(1)
    
    workload.stop()
    if (not test):
        agent_mn1.model.save_models(result_dir + agent_mn1.service_name + "_" + str(seed))
    print(datetime.datetime.now())