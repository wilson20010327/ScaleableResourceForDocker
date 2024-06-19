# DRL Scalable Computer Resource
## Setup 
1. [Download dockermachine, create three docker machine and group a docker swarm](https://hackmd.io/3w5OdQ__Tre7Guy5hT-vmg)
2. Copy docker-compose-mn1.yml and docker-compose-mn2.yml into docker swarm master
3. Enter docker swarm master(in our project we set the 'default' as master) run service command 
```=shell
sudo docker-machine ssh default
docker stack deploy --compose-file docker-compose-mn2.yml app 
docker stack deploy --compose-file docker-compose-mn1.yml app 
```
4. Check whether server is setup successfully in browser<br>
("serverIP":"port"/replica"number"/webpage)<br>
http://192.168.99.102:8000/replicas3/webpage<br>
http://192.168.99.103:8001/replicas3/webpage<br>
## Small talk
* Why we run all container without using dockerswarm default horizon scaling?
    1. We find the docker swarm default proxy (requests send to same port and it will redirect to different replicas of container) will create uncontrolable delay when it receive too many requests for long time.
    2. We create three containers and one proxy for both mn1 and mn2 initaly, and in the proxy we define different ports to send to different amounts of containers, then we assume it as the replacement of the default horizon scaling.    