from flask import Flask, request, jsonify
# import cpuUsageCreator 
import requests
import os
import random
data_format = ["cpu_num", "time_long","cpu_usage"]
app = Flask(__name__)
reportRate=os.environ.get('reportRate')
if(reportRate==None):
    print('Didin\'t get the environment variable reportRate')
    reportRate=0.2
reportRate=float(reportRate)
reportRate_std_dev = 0.01

mn2Ip=os.environ.get('mn2Ip')
if(mn2Ip==None):
    print('Didin\'t get the environment variable mn2Ip')
    mn2Ip='127.0.0.1'
mn2Port=os.environ.get('mn2Proxy')
if(mn2Port==None):
    print('Didin\'t get the environment variable mn2Proxy')
    mn2Port='8000/'
mn_2url = 'http://'+mn2Ip+':'+mn2Port+'/'
countRequest:int=0
countWeb:int=0
countMonitor:int=0
eratosthenesNum=int(os.environ.get('eratosthenesNum'))
{# stressJob=cpuUsageCreator.StressCreator()

# @app.route('/cpusetting', methods=['POST'])

# def cpusetting():
#     '''
#     Create the workloading on the server

#     client send request to this branch with json format

#     {
#         "cpu_num": 1, # amounts of cpu  

#         "time_long": 30, # the time of this workload will occupy

#         "cpu_usage":50 # the workload each cpu will done
#     }

#     return: the package sends back to the client
#     '''
#     # Get JSON data from the request
#     data = request.get_json()

#     # Process the data (you can customize this part)
#     result = {"message": "Workload done successfully", "data": data}
#     num_cpu=int(data[data_format[0]])
#     time_long=int(data[data_format[1]])
#     cpu_usage=int(data[data_format[2]])
#     print(data[data_format[0]])
#     print(data[data_format[1]])
#     print(data[data_format[2]])
#     if (cpu_usage>0):
#         stressJob.create_job(num_cpu,time_long,cpu_usage)
#         stressJob.run()
#         # Send a POST request to the server
#         partial=random.gauss(mu=reportRate, sigma=reportRate_std_dev)
#         print('Sample error rate ',partial)
#         data[data_format[2]]=int(data[data_format[2]]*partial)
#     else:
#         stressJob.stop()
#     try:
#         # to handle the exception when cannot cennect to mn_2
#         response = requests.post(mn_2url, json=data)
#     except:
#         print("cannot connect to mn_2, check the port in env")

#     # Print the server's response
#     print(response.json())

#     # Convert the result to JSON and send it back to the client
#     return jsonify(result)
}


@app.route('/simplerequest', methods=['POST'])

def simplerequest():
    '''
    Simple respond to the locust to create workload
    '''
    global countRequest
    # Get JSON data from the request
    data = request.get_json()
    countRequest=countRequest+1
    response='no report'
    def eratosthenes(n):
        is_prime = [True] * (n + 1)
        for i in range(2, int(n ** 0.5) + 1):
            if is_prime[i]:
                for j in range(i * i, n + 1, i):
                    is_prime[j] = False
        return [x for x in range(2, n + 1) if is_prime[x]]
    if(random.random()<reportRate):
        mode = data.get('mode', 'replicas1')
        temp=mn_2url+mode+'/simplerequest'
        response = requests.post(temp, json=data)
        response=response.status_code
    # Process the data (you can customize this part)
    result = {"message": "Received POST request", "formMN2": response}
    print(result)
    print(eratosthenes(eratosthenesNum))
    # Convert the result to JSON and send it back to the client
    return jsonify(result)
@app.route('/calculateRT', methods=['POST'])

def calculateRT():
    '''
    It is just for the client to measure the respond time from the server
    '''
    global countMonitor
    # Get JSON data from the request
    data = request.get_json()
    countMonitor=1+countMonitor
    response='no report'
    # Process the data (you can customize this part)
    result = {"message": "Received POST request"}
    print(result)
    # Convert the result to JSON and send it back to the client
    return jsonify(result)
@app.route("/webpage")  
def home():
    global countRequest,countMonitor,countWeb
    countWeb=1+countWeb
    return "Hello! this is the MN1 page <h1>HELLO</h1><br>"+\
            "Count Request from workload creater: " +str(countRequest)+"<br>"+\
            "Count Web Request: " +str(countWeb)+"<br>"+\
            "Count Request from monitor: " +str(countMonitor)+"<br>"+\
            "Request will caculate prime number: 1 ~ "+str(eratosthenesNum)+"<br>"

if __name__ == '__main__':
    
    port=os.environ.get('mn1Port')
    if(port==None):
        print('Didin\'t get the environment variable mn1Port')
        port=5000  
    app.run(host='0.0.0.0',port=port)