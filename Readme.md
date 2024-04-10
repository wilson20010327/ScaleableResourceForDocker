# ScaleAbleResouceDocker
## simple inroduce of the dir
* ENV_Docker: contain the docker file to create the docker image and the
compose file to setup the docker container in the docker swarm
* model: contain two type of model mpdqn and pdqn two type of drl model
* plot_item: tool to draw plot
* utility: tools to create locust test and tool to get env response time
* agent: the player using model to scale the env
* env: the interface for getting information about enviornment
* main: the entry of this project and this part is seemed as a timer
* sendrequest: create the workload
* setting: use to set parameter for the hole project
## Class Introduction
### env
* __ init __: initial the env variable
* reset: reset env with the given replica and cpus number
* action: scale the env with the given replica and cpus number, different ot reset is reset will first scale to 0 then scale to given repilca
* save_cpu_usage: save the cpu usage data in docker stats to disk   
* save_reponse_time: save the response time data to disk,and return response time data
* get_cpu_utilization_from_data: collect the last five cpu usage data from disk (how many file to collect is according to replica number), return the mean of the collection
* get_state: use the previous function get the state value and calculate the reward with some mathemtic function, return state, reward, reward_perf, reward_res  
### agent
* __ init __: initial the agent variable
* set_model: set the parameter of the model
* step: make the model step
* next: save the cur state and action to another variable 
* act: use the model to create action according to given state and save the action to the self.action, return replica, cpus
* store_trajectory: 