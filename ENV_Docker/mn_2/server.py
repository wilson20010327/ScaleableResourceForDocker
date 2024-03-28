from flask import Flask, request, jsonify
import cpuUsageCreator

import os
data_format = ["cpu_num", "time_long","cpu_usage"]
app = Flask(__name__)
countRequest:int=0
countWeb:int=0
countMonitor:int=0
eratosthenesNum=int(os.environ.get('eratosthenesNum'))
{# Old method 
# stressJob=cpuUsageCreator.StressCreator()
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
#     data = request.get_json()

#     # Process the data (you can customize this part)
#     result = {"message": "Workload done successfully", "data": data}
#     num_cpu=int(data[data_format[0]])
#     time_long=int(data[data_format[1]])
#     cpu_usage=int(data[data_format[2]])
#     print(data[data_format[0]])
#     print(data[data_format[1]])
#     print(data[data_format[2]])
#     if(cpu_usage>0):
#         stressJob.create_job(num_cpu,time_long,cpu_usage)
#         stressJob.run()
#     else:
#         stressJob.stop()
#     # Convert the result to JSON and send it back to the client
#     return jsonify(result)
}

@app.route('/simplerequest', methods=['POST'])

def simplerequest():
    
    '''
    Simple reponse to the request

    It is just for the client to measure the respond time from the server
    '''
    global countRequest
    # Get JSON data from the request
    data = request.get_json()
    countRequest=countRequest+1
    # Process the data (you can customize this part)
    result = {"message": "Received POST request"}
    def eratosthenes(n):
        is_prime = [True] * (n + 1)
        for i in range(2, int(n ** 0.5) + 1):
            if is_prime[i]:
                for j in range(i * i, n + 1, i):
                    is_prime[j] = False
        return [x for x in range(2, n + 1) if is_prime[x]]
    # Convert the result to JSON and send it back to the client
    print(eratosthenes(eratosthenesNum))
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
    # Process the data (you can customize this part)
    result = {"message": "Received POST request"}

    # Convert the result to JSON and send it back to the client
    return jsonify(result)
@app.route("/webpage")  
def home():
    # make sure server is ready to serve
    global countRequest,countMonitor,countWeb
    countWeb=1+countWeb
    return "Hello! this is the MN2 page <h1>HELLO</h1><br>"+\
            "Count Request from workload creater: " +str(countRequest)+"<br>"+\
            "Count Web Request: " +str(countWeb)+"<br>"+\
            "Count Request from monitor: " +str(countMonitor)+"<br>"+\
            "Request will caculate prime number: 1 ~ "+str(eratosthenesNum)+"<br>"
if __name__ == '__main__':
    
    port=os.environ.get('mn2Port')
    if(port==None):
        print('Didin\'t get the environment variable mn2Port')
        port=5500
    app.run(host='0.0.0.0',port=port)