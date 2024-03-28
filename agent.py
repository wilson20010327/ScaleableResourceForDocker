import random
import numpy as np
from model.pdqn_v1 import PDQNAgent
from model.pdqn_multipass import MultiPassPDQNAgent
class agent():
    def __init__(self,result_dir,service_name,n_state,n_actions,test) :
        self.state_prev=[]
        self.action_prev=[] #[act, act_param, all_action_parameters, if_epsilon]
        self.action=[] #[act, act_param, all_action_parameters, if_epsilon]
        self.state=[]
        self.result_dir=result_dir
        self.service_name=service_name
        self.n_state=n_state
        self.n_actions=n_actions
        self.test=test
        # self.epsilon=0.1
    def set_model(self, epsilon_initial,batch_size, gamma, initial_memory_threshold,
                    replay_memory_size, epsilon_steps, tau_actor, tau_actor_param, use_ornstein_noise, learning_rate_actor,
                    learning_rate_actor_param, epsilon_final,
                    clip_grad, layers, multipass, action_input_layer, seed):
        model_pick=PDQNAgent
        if multipass:
            model_pick=MultiPassPDQNAgent
        self.model = model_pick(
                       self.n_state, self.n_actions,
                       batch_size=batch_size,
                       learning_rate_actor=learning_rate_actor,
                       learning_rate_actor_param=learning_rate_actor_param,
                       epsilon_initial=epsilon_initial,
                       epsilon_steps=epsilon_steps,
                       gamma=gamma,
                       tau_actor=tau_actor,
                       tau_actor_param=tau_actor_param,
                       clip_grad=clip_grad,
                       initial_memory_threshold=initial_memory_threshold,
                       use_ornstein_noise=use_ornstein_noise,
                       replay_memory_size=replay_memory_size,
                       epsilon_final=epsilon_final,
                       actor_kwargs={'hidden_layers': layers,
                                     'action_input_layer': action_input_layer},
                       actor_param_kwargs={'hidden_layers': layers,
                                           'squashing_function': True,
                                           'output_layer_init_std': 0.0001},
                       seed=seed,
                       service_name=self.service_name,
                       result_dir=self.result_dir)
        if self.test:  # Test
            parts = self.result_dir.rsplit('/', 2)
            result_dir_ = parts[0] + '/'
            # print(result_dir_)
            self.model.load_models(result_dir_ + self.service_name + "_" + str(seed))
            self.model.epsilon_final = 0.
            self.model.epsilon = 0.
            self.model.noise = None   
    def step (self,next_state,reward,done):
        # update parameter
        #[act, act_param, all_action_parameters, if_epsilon]
        self.model.step(self.state, (self.action_prev[0], self.action_prev[2]), reward, next_state,
                                   (self.action_prev[0], self.action_prev[2]), done)
        print('step')
    def next(self):
        self.action_prev=self.action
        self.state_prev=self.state
    def pad_action(self,act, act_param):
        params = [np.zeros((1,), dtype=np.float32), np.zeros((1,), dtype=np.float32), np.zeros((1,), dtype=np.float32)]
        params[act][:] = act_param
        return (act, params)
    def act (self,state):
        # output action
        self.state=state
        act, act_param, all_action_parameters, if_epsilon = self.model.act(np.array(self.state, dtype=np.float32))
        
        a=[act, act_param, all_action_parameters, if_epsilon]
        action = self.pad_action(act, act_param)
        self.action=a
        print('act')
        return action
    def store_trajectory(self, step, s, a_r, a_c, r, r_perf, r_res, s_, done, if_epsilon):
        path = self.result_dir + self.service_name + "_trajectory.txt"
        tmp_s = list(s)
        tmp_s_ = list(s_)
        a_c_ = list(a_c)
        f = open(path, 'a')
        data = str(step) + ' ' + str(tmp_s) + ' ' + str(a_r) + ' ' + str(a_c_) + ' ' + str(r) + ' ' + str(r_perf) + ' ' + str(r_res) + ' ' + str(tmp_s_) + ' ' + str(done) + ' ' + str(if_epsilon) + '\n'
        f.write(data)
    def print_step(self,step,next_state,reward, reward_perf, reward_res,done):
        print("service name:", self.service_name, "action: ", self.action[0]+1, self.action[1], self.action[2], " step: ", step,
                          " next_state: ",
                          next_state, " reward: ", reward, " done: ", done, "epsilon", self.model.epsilon)
        self.store_trajectory(step, self.state_prev, self.action[0]+1, self.action[2], reward, reward_perf,
                        reward_res,next_state, done, self.action[3])
