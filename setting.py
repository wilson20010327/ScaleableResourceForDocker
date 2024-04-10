import time,os
from sendrequest import workloadcreater
from env import env
from agent import agent
import threading
import numpy as np
import datetime
print(datetime.datetime.now())
test= True
result_dir = "./result/static80-prime20000/evaluation/" #
# Need modify ip if ip change
# check cmd : sudo docker-machine ls
IP = "192.168.99.102"  # app_mn1
IP1 = "192.168.99.103"  # app_mn2
# request rate r
data_rate = 80 #120     # if not use_tm
ifdynamic=False
dymean=data_rate
dymax=100
dymin=5
request_detail={
    'data_rate': data_rate,
    'ifdynamic': ifdynamic,
    'dymax': dymax,
    'dymin': dymin
}
epochs= 8 #8
if test :
    epochs=1 ###
menitor_period= 30 #30
simulate_time= 3600 #3600
real_run=simulate_time+menitor_period

ini_replica1, ini_cpus1, ini_replica2, ini_cpus2 = 1, 1, 1, 1
# Parameter
# cost weight -------------------
w_perf = 0.5  # 0.7  # 0.5
w_res = 0.5   # 0.3  # 0.5
#  -------------------------------
# Tmax setting : Need modifying for different machine
Tmax_mn1 = 20
Tmax_mn2 = 10 #5
# ------------
timeout_setting = 0.05          #  0.1 / 0.05  # choose 0.05 finally
# T_upper = timeout_setting*1000  #  0.1s to 50 ms
# ------------
error_rate = 0.2  # 0.2 # defective product probability

## Learning parameter
# S ={k, u , c, r} {k, u , c}
# k (replica): 1 ~ 3                          actual value : same
# u (cpu utilization) : 0.0, 0.1 0.2 ...1     actual value : 0 ~ 100
# c (used cpus) : 0.1 0.2 ... 1               actual value : same


multipass = True  # False : PDQN  / Ture: MPDQN

# totoal step = episode per step * episode; ex : 60 * 16 = 960
# Exploration parameters
epsilon_steps = 840  # step per episodes * (episodes-1)
epsilon_initial = 1   #
epsilon_final = 0.01  # 0.01

# Learning rate
learning_rate_actor_param = 0.001  # actor # 0.001
learning_rate_actor = 0.01         # critic # 0.01
# Target Learning rate
tau_actor_param = 0.01    # actor  # 0.01
tau_actor = 0.1           # critic # 0.1

gamma = 0.9               # Discounting rate
replay_memory_size = 960  # Replay memory
batch_size = 16
initial_memory_threshold = 16  # Number of transitions required to start learning
use_ornstein_noise = False
layers = [64,]
seed = 7

clip_grad = 0 # no use now
action_input_layer = 0  # no use now

# check result directory
if os.path.exists(result_dir):
    print("Deleting existing result directory...")
    raise SystemExit  # end process

# build dir
os.mkdir(result_dir)
requestResultFolderPath=result_dir+"requestResultSet/"
os.mkdir(requestResultFolderPath)
# store setting
path = result_dir + "setting.txt"

# Define settings dictionary
settings = {
    'date': datetime.datetime.now(),
    'data_rate': data_rate,
    'ifdynamic': ifdynamic,
    'dymax': str(dymax),
    'dymin': str(dymin),
    'Tmax_mn1': Tmax_mn1,
    'Tmax_mn2': Tmax_mn2,
    'simulate_time': simulate_time,
    'tau_actor': tau_actor,
    'tau_actor_param': tau_actor_param,
    'learning_rate_actor': learning_rate_actor,
    'learning_rate_actor_param': learning_rate_actor_param,
    'gamma': gamma,
    'epsilon_steps': epsilon_steps,
    'epsilon_final': epsilon_final,
    'replay_memory_size': replay_memory_size,
    'batch_size': batch_size,
    'loss_function': 'MSE loss',
    'layers': layers,
    'if_test': test,
    'w_perf': w_perf,
    'w_res': w_res,
}

# Write settings to file
with open(result_dir + 'setting.txt', 'a') as f:
    for key, value in settings.items():
        f.write(f'{key}: {value}\n')