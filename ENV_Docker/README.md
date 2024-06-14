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
## Structure (Two level)
### Mn_1 : handle user's request (simple web server)
* Set the port in docker-compose.yml (default: 5000)
* There are three routers in this web 
    1. <b>cpusetting: </b> send post request with the json format, server will create the workload according to the request, beside it will create the post request to mn_2 to create its workload. And it will return the workload it create to mn_2 to client.
    <pre>
    {
        "cpu_num": 1, # amounts of cpu  
        "time_long": 30, # the time of this workload will occupy
        "cpu_usage":50 # the workload each cpu will done
    }</pre> 
    2. <b>simplerequest: </b> Server return the any package after this route got the post request, it is for user to calculate the respond time. 
    3. <b>webpage: </b> type this on the browser To check whether the server has built 

### Mn_2 : handle mn1's request  (simple web server)
* Set the port in docker-compose.yml (default: 5500)
* There are three routers in this web 
    1. <b>cpusetting: </b> send post request with the json format, server will create the workload according to the request, and it will return the workload.
    <pre>
    {
        "cpu_num": 1, # amounts of cpu  
        "time_long": 30, # the time of this workload will occupy
        "cpu_usage":50 # the workload each cpu will done
    }</pre> 
    2. <b>simplerequest: </b> Server return the any package after this route got the post request, it is for user to calculate the respond time. 
    3. <b>webpage: </b> type this on the browser To check whether the server has built 

Be careful when use docker service scale, because it just creates extra task for other request, however we use the request to create workload, perhaps we need to split the workload request package in to the some number of the relicas. 