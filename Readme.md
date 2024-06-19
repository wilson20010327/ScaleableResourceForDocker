# ScaleAbleResouceDocker
## Setup 
1. Set up the docker swarm check the detail in Readme file in ENV_Docker folder. 
    * Build three VM I called them default(master), worker, ans worker1.
    * Create service on default and because it is the master of docker claster, it can deploy the task to others VM through compose file
1. Create python environment through requirement.txt
1. Set the information of your project in setting.py, below are some basic parameters need to set.
    * test: use to show this run is for train or evaluation, if it is true the program will find model save file in the previous file of result_dir.
    * result_dir: the path you want the result of this run save at, make sure this folder hasn't created yet, or it will return will error.
    * IP & IP1: this specify the IP of worker and worker1 respectivly, it is because we need to send requests to this two VM.
1. Run the DQN or MPDQN project
    * DQN: python DQN_main.py
    * MPDQN: python MPDQN_main.py
1. Wait for about 16 hours 
    * Although the total time we assume is 8*3600 seconds, however, we spend time to wait the container scale.
1. Visualize the output of the trajectory(the state transition in the process)
    * set tmp_dir to your result_dir(the path you set in setting.py) in matplot_trajectory_MPDQN.py
    * run: python matplot_trajectory_MPDQN.py