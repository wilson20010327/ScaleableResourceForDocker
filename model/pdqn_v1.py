import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import random
from model.memory.memory import Memory
from model.utils import soft_update_target_network, hard_update_target_network
from model.utils.noise import OrnsteinUhlenbeckActionNoise

class QActor(nn.Module):
    def __init__(self, state_size, action_size, action_parameter_size, hidden_layers=(100,), action_input_layer=0,
                 output_layer_init_std=None, activation="relu", **kwargs):
        super(QActor, self).__init__()
        self.state_size = state_size
        self.action_size = action_size
        self.action_parameter_size = action_parameter_size
        self.activation = activation
        print("self.state_size: ", self.state_size)
        print("self.action_size: ", self.action_size)
        # create layers
        self.layers = nn.ModuleList()
        inputSize = self.state_size + self.action_parameter_size
        lastHiddenLayerSize = inputSize
        if hidden_layers is not None:
            nh = len(hidden_layers)
            self.layers.append(nn.Linear(inputSize, hidden_layers[0]))
            for i in range(1, nh):
                self.layers.append(nn.Linear(hidden_layers[i - 1], hidden_layers[i]))
            lastHiddenLayerSize = hidden_layers[nh - 1]
        self.layers.append(nn.Linear(lastHiddenLayerSize, self.action_size))

        # initialise layer weights
        for i in range(0, len(self.layers) - 1):
            nn.init.kaiming_normal_(self.layers[i].weight, nonlinearity=activation)
            nn.init.zeros_(self.layers[i].bias)
        if output_layer_init_std is not None:
            nn.init.normal_(self.layers[-1].weight, mean=0., std=output_layer_init_std)

        nn.init.zeros_(self.layers[-1].bias)

    def forward(self, state, action_parameters):
        # implement forward
        # negative_slope = 0.01

        x = torch.cat((state, action_parameters), dim=1)
        num_layers = len(self.layers)
        for i in range(0, num_layers - 1):
            x = F.relu(self.layers[i](x))

        Q = self.layers[-1](x)
        return Q


class ParamActor(nn.Module):

    def __init__(self, state_size, action_size, action_parameter_size, hidden_layers, squashing_function=True,
                 output_layer_init_std=None, init_type="kaiming", activation="relu", init_std=None):
        super(ParamActor, self).__init__()

        self.state_size = state_size
        self.action_size = action_size
        self.action_parameter_size = action_parameter_size
        self.squashing_function = squashing_function
        self.activation = activation
        if init_type == "normal":
            assert init_std is not None and init_std > 0
        # assert self.squashing_function is False  # unsupported, cannot get scaling right yet

        # create layers
        self.layers = nn.ModuleList()
        inputSize = self.state_size
        lastHiddenLayerSize = inputSize
        if hidden_layers is not None:
            nh = len(hidden_layers)
            self.layers.append(nn.Linear(inputSize, hidden_layers[0]))
            for i in range(1, nh):
                self.layers.append(nn.Linear(hidden_layers[i - 1], hidden_layers[i]))
            lastHiddenLayerSize = hidden_layers[nh - 1]
        self.action_parameters_output_layer = nn.Linear(lastHiddenLayerSize, self.action_parameter_size)
        self.action_parameters_passthrough_layer = nn.Linear(self.state_size, self.action_parameter_size)

        # initialise layer weights
        for i in range(0, len(self.layers)):
            if init_type == "kaiming":
                nn.init.kaiming_normal_(self.layers[i].weight, nonlinearity=activation)
            elif init_type == "normal":
                nn.init.normal_(self.layers[i].weight, std=init_std)
            else:
                raise ValueError("Unknown init_type "+str(init_type))
            nn.init.zeros_(self.layers[i].bias)
        if output_layer_init_std is not None:
            nn.init.normal_(self.action_parameters_output_layer.weight, std=output_layer_init_std)
        else:
            nn.init.zeros_(self.action_parameters_output_layer.weight)
        nn.init.zeros_(self.action_parameters_output_layer.bias)

        nn.init.zeros_(self.action_parameters_passthrough_layer.weight)
        nn.init.zeros_(self.action_parameters_passthrough_layer.bias)

        # fix passthrough layer to avoid instability, rest of network can compensate
        # self.action_parameters_passthrough_layer.requires_grad = False
        # self.action_parameters_passthrough_layer.weight.requires_grad = False
        # self.action_parameters_passthrough_layer.bias.requires_grad = False

    def forward(self, state):
        x = state
        negative_slope = 0.01
        num_hidden_layers = len(self.layers)
        for i in range(0, num_hidden_layers):
            if self.activation == "relu":
                x = F.relu(self.layers[i](x))
            elif self.activation == "leaky_relu":
                x = F.leaky_relu(self.layers[i](x), negative_slope)
            else:
                raise ValueError("Unknown activation function "+str(self.activation))
        action_params = self.action_parameters_output_layer(x)
        action_params += self.action_parameters_passthrough_layer(state)

        if self.squashing_function:
            action_params = action_params.sigmoid()  # [0, 1]

        return action_params


class PDQNAgent:
    """
    DDPG actor-critic agent for parameterised action spaces
    [Hausknecht and Stone 2016]
    """
    NAME = "P-DQN Agent"

    def __init__(self,
                 observation_space,
                 action_space,
                 actor_class=QActor,
                 actor_kwargs={},
                 actor_param_class=ParamActor,
                 actor_param_kwargs={},
                 epsilon_initial=1.0,
                 epsilon_final=0.05,
                 epsilon_steps=10000,
                 batch_size=64,
                 gamma=0.99,
                 tau_actor=0.01,  # Polyak averaging factor for copying target weights
                 tau_actor_param=0.001,
                 replay_memory_size=1000000,
                 learning_rate_actor=0.0001,
                 learning_rate_actor_param=0.00001,
                 initial_memory_threshold=0,
                 use_ornstein_noise=True,  # if false, uses epsilon-greedy with uniform-random action-parameter exploration
                 loss_func=F.mse_loss, # F.mse_loss
                 clip_grad=10,
                 inverting_gradients=False,
                 zero_index_gradients=False,
                 indexed=False,
                 weighted=False,
                 average=False,
                 random_weighted=False,
                 device="cuda" if torch.cuda.is_available() else "cpu",
                 seed=None,
                 service_name='app_mn1',
                 result_dir="./"):
        # super(PDQNAgent, self).__init__(observation_space, action_space)
        self.observation_space = observation_space
        self.action_space = action_space
        self.device = torch.device(device)
        self.num_actions = action_space
        self.action_parameter_sizes = np.array([1 for i in range(1,self.num_actions+1)])
        self.action_parameter_size = int(self.action_parameter_sizes.sum())
        # print("====================================================")
        # print(self.action_parameter_sizes, self.action_parameter_size)
        # self.action_max = torch.from_numpy(np.ones((self.num_actions,))).float().to(device)
        # self.action_min = -self.action_max.detach()
        # self.action_range = (self.action_max-self.action_min).detach()
        # print(np.array([1.], dtype=np.float32) for i in range(1, self.num_actions + 1))
        self.action_parameter_max_numpy = np.concatenate([np.array([1.], dtype=np.float32) for i in range(1, self.num_actions+1)]).ravel()  # 1 : para max
        self.action_parameter_min_numpy = np.concatenate([np.array([0.8], dtype=np.float32) for i in range(1, self.num_actions+1)]).ravel()  # 0.5 : para min
        self.action_parameter_range_numpy = (self.action_parameter_max_numpy - self.action_parameter_min_numpy)
        self.action_parameter_max = torch.from_numpy(self.action_parameter_max_numpy).float().to(device)
        self.action_parameter_min = torch.from_numpy(self.action_parameter_min_numpy).float().to(device)
        self.action_parameter_range = torch.from_numpy(self.action_parameter_range_numpy).float().to(device)
        # print("----------------------------------------------------------------------------------------------")
        # print(self.action_parameter_max_numpy, self.action_parameter_min_numpy, self.action_parameter_range_numpy,
        #      self.action_parameter_max, self.action_parameter_min, self.action_parameter_range)

        self.epsilon = epsilon_initial
        self.epsilon_initial = epsilon_initial
        self.epsilon_final = epsilon_final
        self.epsilon_steps = epsilon_steps
        self.indexed = indexed
        self.weighted = weighted
        self.average = average
        self.random_weighted = random_weighted
        assert (weighted ^ average ^ random_weighted) or not (weighted or average or random_weighted)

        self.action_parameter_offsets = self.action_parameter_sizes.cumsum()
        self.action_parameter_offsets = np.insert(self.action_parameter_offsets, 0, 0)

        self.batch_size = batch_size
        self.gamma = gamma
        self.replay_memory_size = replay_memory_size
        self.initial_memory_threshold = initial_memory_threshold
        self.learning_rate_actor = learning_rate_actor
        self.learning_rate_actor_param = learning_rate_actor_param
        self.inverting_gradients = inverting_gradients
        self.tau_actor = tau_actor
        self.tau_actor_param = tau_actor_param
        self._step = 0
        self._episode = 0
        self.updates = 0
        self.clip_grad = clip_grad
        self.zero_index_gradients = zero_index_gradients

        self.np_random = None
        self.seed = seed
        self._seed(seed)
        self.result_dir=result_dir

        self.use_ornstein_noise = use_ornstein_noise
        self.noise = OrnsteinUhlenbeckActionNoise(self.action_parameter_size, random_machine=self.np_random, mu=0., theta=0.15, sigma=0.0001) #, theta=0.01, sigma=0.01)
        # print(self.num_actions+self.action_parameter_size)

        self.replay_memory = Memory(replay_memory_size, (observation_space,), (1+self.action_parameter_size,), next_actions=False)
        self.actor = actor_class(self.observation_space, self.num_actions, self.action_parameter_size, **actor_kwargs).to(device)
        self.actor_target = actor_class(self.observation_space, self.num_actions, self.action_parameter_size, **actor_kwargs).to(device)
        hard_update_target_network(self.actor, self.actor_target)
        self.actor_target.eval()

        self.actor_param = actor_param_class(self.observation_space, self.num_actions, self.action_parameter_size, **actor_param_kwargs).to(device)
        self.actor_param_target = actor_param_class(self.observation_space, self.num_actions, self.action_parameter_size, **actor_param_kwargs).to(device)
        hard_update_target_network(self.actor_param, self.actor_param_target)
        self.actor_param_target.eval()

        self.loss_func = loss_func  # l1_smooth_loss performs better but original paper used MSE
        self.service_name = service_name
        # Original DDPG paper [Lillicrap et al. 2016] used a weight decay of 0.01 for Q (critic)
        # but setting weight_decay=0.01 on the critic_optimiser seems to perform worse...
        # using AMSgrad ("fixed" version of Adam, amsgrad=True) doesn't seem to help either...
        self.actor_optimiser = optim.Adam(self.actor.parameters(), lr=self.learning_rate_actor) #, betas=(0.95, 0.999))
        self.actor_param_optimiser = optim.Adam(self.actor_param.parameters(), lr=self.learning_rate_actor_param) #, betas=(0.95, 0.999)) #, weight_decay=critic_l2_reg)

    def _seed(self, seed=None):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        self.np_random = np.random.RandomState(seed=seed)
        if seed is not None:
            torch.manual_seed(seed)
            if self.device == torch.device("cuda"):
                torch.cuda.manual_seed(seed)

    def _ornstein_uhlenbeck_noise(self, all_action_parameters):
        """ Continuous action exploration using an Ornstein–Uhlenbeck process. """
        return all_action_parameters.data.numpy() + (self.noise.sample() * self.action_parameter_range_numpy)

    def epsilon_decay(self):
        step = self._step
        if step < self.epsilon_steps:
            self.epsilon = self.epsilon_initial - (self.epsilon_initial - self.epsilon_final) * (
                    step / self.epsilon_steps)
        else:
            self.epsilon = self.epsilon_final

    def act(self, state):
        with torch.no_grad():
            state = torch.from_numpy(state).to(self.device)
            all_action_parameters = self.actor_param.forward(state)
            if_epsilon = False
            # Hausknecht and Stone [2016] use epsilon greedy actions with uniform random action-parameter exploration
            rnd = self.np_random.uniform()
            if rnd < self.epsilon:
                if_epsilon = True
                action = self.np_random.choice(self.num_actions)
                if not self.use_ornstein_noise:
                    all_action_parameters = torch.from_numpy(np.random.uniform(self.action_parameter_min_numpy,
                                                              self.action_parameter_max_numpy))
            else:
                # select maximum action
                Q_a = self.actor.forward(state.unsqueeze(0), all_action_parameters.unsqueeze(0))
                Q_a = Q_a.detach().cpu().data.numpy()
                action = np.argmax(Q_a)

                # scale action from [0, 1] to [0.8, 1]
                output_min = 0  # sigmoid min
                output_max = 1  # sigmoid max
                action_min = 0.8  # ACTION SPACE min   # 0.5
                action_max = 1  # ACTION SPACE max
                all_action_parameters = ((all_action_parameters - output_min) * (action_max - action_min) / (
                            output_max - output_min)) + action_min

            # add noise only to parameters of chosen action
            all_action_parameters = all_action_parameters.cpu().data.numpy()
            offset = np.array([self.action_parameter_sizes[i] for i in range(action)], dtype=int).sum()
            if self.use_ornstein_noise and self.noise is not None:
                all_action_parameters[offset:offset + self.action_parameter_sizes[action]] += self.noise.sample()[offset:offset + self.action_parameter_sizes[action]]
            # # clip action
            # all_action_parameters = np.clip(all_action_parameters, 0.5, 1.0)
            action_parameters = all_action_parameters[offset:offset+self.action_parameter_sizes[action]]


        return action, action_parameters, all_action_parameters, if_epsilon


    def step(self, state, action, reward, next_state, next_action, terminal):
        act, all_action_parameters = action
        self._step += 1

        # self._add_sample(state, np.concatenate((all_actions.data, all_action_parameters.data)).ravel(), reward, next_state, terminal)
        self._add_sample(state, np.concatenate(([act], all_action_parameters)).ravel(), reward, next_state, np.concatenate(([next_action[0]],next_action[1])).ravel(), terminal=terminal)
        if self._step >= self.batch_size and self._step >= self.initial_memory_threshold:
            self._optimize_td_loss()
            self.updates += 1

    def _add_sample(self, state, action, reward, next_state, next_action, terminal):
        assert len(action) == 1 + self.action_parameter_size
        self.replay_memory.append(state, action, reward, next_state, terminal=terminal)

    def _optimize_td_loss(self):
        if self._step < self.batch_size or self._step < self.initial_memory_threshold:
            return
        # Sample a batch from replay memory
        states, actions, rewards, next_states, terminals = self.replay_memory.sample(self.batch_size, random_machine=self.np_random)

        states = torch.from_numpy(states).to(self.device)
        actions_combined = torch.from_numpy(actions).to(self.device)  # make sure to separate actions and parameters
        actions = actions_combined[:, 0].long()
        action_parameters = actions_combined[:, 1:]
        rewards = torch.from_numpy(rewards).to(self.device).squeeze()
        next_states = torch.from_numpy(next_states).to(self.device)
        terminals = torch.from_numpy(terminals).to(self.device).squeeze()

        # ---------------------- optimize Q-network ----------------------
        with torch.no_grad():
            pred_next_action_parameters = self.actor_param_target.forward(next_states)
            pred_Q_a = self.actor_target(next_states, pred_next_action_parameters)
            Qprime = torch.max(pred_Q_a, 1, keepdim=True)[0].squeeze()

            # Compute the TD error
            target = rewards + (1 - terminals) * self.gamma * Qprime

        # Compute current Q-values using policy network
        q_values = self.actor(states, action_parameters)
        y_predicted = q_values.gather(1, actions.view(-1, 1)).squeeze()  # Select the corresponding action q value
        y_expected = target
        loss_Q = self.loss_func(y_predicted, y_expected)

        self.actor_optimiser.zero_grad()
        loss_Q.backward()
        if self.clip_grad > 0:
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), self.clip_grad)
        self.actor_optimiser.step()

        # ---------------------- optimize actor ----------------------

        action_params = self.actor_param(states)

        Q = self.actor(states, action_params)
        Q_val = Q
        Q_loss = -torch.mean(torch.sum(Q_val, 1))

        self.actor_param_optimiser.zero_grad()
        Q_loss.backward()

        if self.clip_grad > 0:
            torch.nn.utils.clip_grad_norm_(self.actor_param.parameters(), self.clip_grad)

        self.actor_param_optimiser.step()

        soft_update_target_network(self.actor, self.actor_target, self.tau_actor)
        soft_update_target_network(self.actor_param, self.actor_param_target, self.tau_actor_param)
        self.store_critic_loss(loss_Q)
        self.store_actor_loss(Q_loss)


    def save_models(self, prefix):
        torch.save(self.actor.state_dict(), prefix + '_actor.pt')
        torch.save(self.actor_param.state_dict(), prefix + '_actor_param.pt')
        print('Models saved successfully')

    def load_models(self, prefix):
        self.actor.load_state_dict(torch.load(prefix + '_actor.pt'))
        self.actor_param.load_state_dict(torch.load(prefix + '_actor_param.pt'))
        print('Models loaded successfully')

    def store_actor_loss(self, loss):
        # Write the string to a text file
        path = self.result_dir + self.service_name + "_actor_loss.txt"
        #path = "actor_loss.txt"
        f = open(path, 'a')
        data = str(loss) + '\n'
        f.write(data)

    def store_critic_loss(self, loss):
        # Write the string to a text file
        path = self.result_dir + self.service_name + "_critic_loss.txt"
        # path = "critic_loss.txt"
        f = open(path, 'a')
        data = str(loss) + '\n'
        f.write(data)