import requests
import json
import time

# def control_server_workload(url: str,time_long:int,cpu_usage:int):
#     '''
#     send post request to the url/cpusetting to set the workload on server(with creating workload by stress_ng)
#     url: server ip:port
#     time_long: time the workload occupy, if 0 mean to work for ever
#     cpu_usage: the cpu percentage the workload is create
#     return: server's respond json 
#     '''
#     # # Specify the server URL
#     # url = 'http://0.0.0.0:5000/simplerequest'
#     url = url+'/cpusetting'
#     # Define the data to be sent in JSON format
#     data = {"cpu_num": 1, "time_long": time_long,"cpu_usage":cpu_usage}

#     # Send a POST request to the server
#     response = requests.post(url, json=data)

#     # Print the server's response
#     print(response.json())
def get_respond_time(url: str,timeout:float):
    # # Specify the server URL
    # url = 'http://0.0.0.0:5000/simplerequest'
    url = url+'/calculateRT'
    # Define the data to be sent in JSON format
    data = {"data": 'simple request package'}

    # Send a POST request to the server
    start = time.time()
    response = requests.post(url, json=data,timeout=timeout)
    end =time.time()
    rt=end-start
    if rt>0.05:
        rt=0.05
    # Print the server's response
    print(response.status_code)
    return response.status_code,rt




if __name__ == '__main__':
    url = 'http://127.0.0.1:5000' 
    url='http://192.168.99.102:5000'
    print(get_respond_time(url,2))
    
    # print(get_respond_time(url,0.05))
    # time.sleep(20)
    # print(control_server_workload(url,30,0))