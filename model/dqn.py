import torch
from torch import nn 
import torch.optim as optim
import torch.nn.functional as F
from model.memory.memory import Memory
import numpy as np
from model.utils import soft_update_target_network, hard_update_target_network
import math
import random
BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 1000
TAU = 0.005
LR = 1e-4
steps_done = 0
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
result_dir="./"
class DQN(nn.Module):
    def __init__(self, n_observations,n_actions,hidden_layers):
        super(DQN, self).__init__()
        self.layer1=nn.Linear(n_observations,hidden_layers)
        self.layer2=nn.Linear(hidden_layers,hidden_layers)
        self.layer3=nn.Linear(hidden_layers,n_actions)
    def forward(self,x):
        x=F.relu(self.layer1(x))
        x=F.relu(self.layer2(x))
        return self.layer3(x)

class Agent():
    def __init__(self,service_name,n_observations,n_actions,hidden_layers,result_dir="",train=True,replay_memory_size=10000,batch_size=128):

        self.train=train
        self.service_name = service_name
        self.result_dir = result_dir
        self.Q=DQN(n_observations,n_actions,hidden_layers)
        self.target_Q=DQN(n_observations,n_actions,hidden_layers)
        if not self.train:
            self.load_models(result_dir+"/../")
        hard_update_target_network(self.Q, self.target_Q)
        self.target_Q.eval()
        self.learning_rate_Q=0.0001
        # self.learning_rate_actor_param=0.00001,
        self.Q_optimiser = optim.Adam(self.Q.parameters(), lr=self.learning_rate_Q) 
        # self.actor_param_optimiser = optim.Adam(self.actor_param.parameters(), lr=self.learning_rate_actor_param) 
        self.loss_func=F.mse_loss

        self.memory=Memory(replay_memory_size, (n_observations,), (1,), next_actions=False,dtype='int64')
        self.batch_size=batch_size
        self._step = 0
        self._episode = 0
        self.updates =0
        self.state_prev=[]
        self.action_prev=0
        self.action=0
        self.state=[]
    def next(self):
        self.action_prev=np.array(self.action, dtype=np.int32).item()     
        self.state_prev=np.array(self.state, dtype=np.float32).squeeze(0).tolist()     
        pass   
    def select_action(self,state,env=None):
        global steps_done
        state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
        self.state=state
        sample = random.random()
        eps_threshold = EPS_END + (EPS_START - EPS_END) * \
            math.exp(-1. * steps_done / EPS_DECAY)
        steps_done += 1
        if (not self.train) or sample > eps_threshold:
            with torch.no_grad():
                # t.max(1) will return the largest column value of each row.
                # second column on max result is index of where max element was
                # found, so we pick action with the larger expected reward.
                print('best')
                self.action=self.Q(state).max(1).indices.view(1, 1)
                return self.action
        else:
            self.action=torch.tensor([[random.randint(0,4)]], device=device, dtype=torch.int64)
            return self.action
    
    def add_memory(self,state,action,reward,new_state,terminal):
        # print(action.squeeze(0),reward)
        self.memory.append(state, action, reward, new_state, terminal=terminal)

    def step(self,new_state,reward,terminal):
        self._step+=1
        # print(action)
        if self.train:
            self.add_memory(self.state,self.action_prev,reward,new_state,terminal)
            if (self._step<self.batch_size): 
                # print('memory cannot fail the batch')
                return
            self._optimize_td_loss()
            self.updates += 1

    def _optimize_td_loss(self):
        states, actions, rewards, next_states, terminals = self.memory.sample(self.batch_size)
        # print(actions)
        states = torch.from_numpy(states).to(device)
        actions = torch.from_numpy(actions).to(device) # make sure to separate actions and parameters
        rewards = torch.from_numpy(rewards).to(device).squeeze()
        next_states = torch.from_numpy(next_states).to(device)
        terminals = torch.from_numpy(terminals).to(device).squeeze()
        
        with torch.no_grad():
            pred_Q_a = self.target_Q.forward(next_states)
            Qprime = torch.max(pred_Q_a, 1, keepdim=True)[0].squeeze()
            
            # Compute the TD error
            target = rewards + (1 - terminals) * GAMMA * Qprime
            # print (next_states,terminals,pred_Q_a,Qprime,target)
        
        q_values = self.Q.forward(states)
        # print(self._step)
        # print(states,target)
        # print(q_values,actions)
        y_predicted = q_values.gather(1, actions).squeeze(1)  # Select the corresponding action q value
        
        y_expected = target
        # print(y_predicted,y_expected)
        loss_Q = self.loss_func(y_predicted, y_expected)
        self.Q_optimiser.zero_grad()
        loss_Q.backward()
        torch.nn.utils.clip_grad_value_(self.Q.parameters(), 100)
        self.Q_optimiser.step()

        target_net_state_dict = self.target_Q.state_dict()
        policy_net_state_dict = self.Q.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*TAU + target_net_state_dict[key]*(1-TAU)
        self.target_Q.load_state_dict(target_net_state_dict)
        pass
    def store_trajectory(self, step, s, a_r, a_c, r, r_perf, r_res, s_, done, if_epsilon):
        path = self.result_dir + self.service_name + "_trajectory.txt"
        tmp_s = s
        tmp_s_ = list(s_)
        a_c_ = list(a_c)
        f = open(path, 'a')
        data = str(step) + ' ' + str(tmp_s) + ' ' + str(a_r) + ' ' + str(a_c_) + ' ' + str(r) + ' ' + str(r_perf) + ' ' + str(r_res) + ' ' + str(tmp_s_) + ' ' + str(done) + ' ' + str(if_epsilon) + '\n'
        f.write(data)
    def print_step(self,step,next_state,reward, reward_perf, reward_res,done):
        temp=[0,0.1,-0.1,1,-1]
        
        print("service name:", self.service_name, "action: ", self.action_prev," ",temp[self.action_prev], " step: ", step,
                          " next_state: ",
                          next_state, " reward: ", reward, " done: ", done)
        self.store_trajectory(step, self.state_prev, self.action_prev, [0,0.1,-0.1,1,-1], reward, reward_perf,
                        reward_res,next_state, done, "NONE")
        
    def save_model(self, prefix=''):
        torch.save(self.Q.state_dict(), prefix +  'Q.pt')
        print('Models saved successfully')
    def load_models(self, prefix=''):
        self.Q.load_state_dict(torch.load(prefix + self.service_name + "_" + str(7)+'Q.pt'))
        print('Models loaded successfully')

# def plot_durations(show_result=False):
#     plt.figure(1)
#     durations_t = torch.tensor(episode_durations, dtype=torch.float)
#     if show_result:
#         plt.title('Result')
#     else:
#         plt.clf()
#         plt.title('Training...')
#     plt.xlabel('Episode')
#     plt.ylabel('Duration')
#     plt.plot(durations_t.numpy())
#     # Take 100 episode averages and plot them too
#     if len(durations_t) >= 100:
#         means = durations_t.unfold(0, 100, 1).mean(1).view(-1)
#         means = torch.cat((torch.zeros(99), means))
#         plt.plot(means.numpy())

#     plt.pause(0.001)  # pause a bit so that plots are updated
#     if is_ipython:
#         if not show_result:
#             display.display(plt.gcf())
#             display.clear_output(wait=True)
#         else:
#             display.display(plt.gcf())
# # if __name__ =='__main__':
# #     import gymnasium as gym
# #     import math
# #     import random
# #     import matplotlib
# #     import matplotlib.pyplot as plt
# #     from collections import namedtuple, deque
# #     from itertools import count
# #     env = gym.make("CartPole-v1")
# #     # set up matplotlib
# #     is_ipython = 'inline' in matplotlib.get_backend()
# #     if is_ipython:
# #         from IPython import display

# #     plt.ion()

# #     # if GPU is to be used
    
# #     n_actions = env.action_space.n
# #     # Get the number of state observations
# #     state, info = env.reset()
# #     n_observations = len(state)
# #     agent=Agent(n_observations,n_actions,128,result_dir,False)

# #     episode_durations = []
# #     if torch.cuda.is_available():
# #         num_episodes = 1
# #     else:
# #         num_episodes = 1

# #     for i_episode in range(num_episodes):
# #         # Initialize the environment and get its state
# #         state, info = env.reset()
# #         state = torch.tensor(state, dtype=torch.float32, device=device).unsqueeze(0)
# #         for t in count():
# #             action =int( agent.select_action(state,env).item())
            
# #             observation, reward, terminated, truncated, _ = env.step(action)
# #             reward = torch.tensor([reward], device=device)
# #             action = torch.tensor([action], device=device)
# #             done = 0
# #             if (terminated or truncated):
# #                 done=1
            
# #             next_state = torch.tensor(observation, dtype=torch.float32, device=device).unsqueeze(0)

# #             # Store the transition in memory
# #             print(state)
# #             agent.step(state,action,reward,next_state,done)
            

# #             # Move to the next state
# #             state = next_state

# #             if done:
# #                 episode_durations.append(t + 1)
# #                 plot_durations()
# #                 break
# #     if(agent.train):
# #         agent.save_model()
# #     print('Complete')
# #     plot_durations(show_result=True)
# #     plt.ioff()
# #     plt.show()