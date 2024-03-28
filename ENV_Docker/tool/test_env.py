import subprocess,json,statistics
result_dir = "./"
# cmd = "sudo docker-machine ssh " + "worker1" + " docker stats --no-stream --format \\\"{{ json . }}\\\" "

# timestamp = 1
# returned_text = subprocess.check_output(cmd, shell=True)
# my_data = returned_text.decode('utf8')
# # print(my_data.find("CPUPerc"))
# my_data = my_data.split("}")
# # state_u = []
# for i in range(len(my_data) - 1):
#     # print(my_data[i]+"}")
#     my_json = json.loads(my_data[i] + "}")
#     name = my_json['Name'].split(".")[0]
#     cpu = my_json['CPUPerc'].split("%")[0]
#     if "app_mn" in name and float(cpu) > 0:
#         path = result_dir + name + "_cpu.txt"
#         f = open(path, 'a')
#         data = str(timestamp) + ' '
#         data = data + str(cpu) + ' ' + '\n'

#         f.write(data)
#         f.close()

def get_cpu_utilization_from_data(service_name,replica):
        path:list= [result_dir + service_name + '-1_cpu.txt',
                    result_dir + service_name + '-2_cpu.txt',
                    result_dir + service_name + '-3_cpu.txt']
        try:
            last_avg_cpu=[]
            for i in range(replica):
                print(path[i])
                f = open(path[i], "r")
                cpu = []
                time = []
                for line in f:
                    s = line.split(' ')
                    time.append(float(s[0]))
                    cpu.append(float(s[1]))
                # Get last five data
                last_avg_cpu.append(statistics.mean(cpu[-5:]))  # might be wrong if there are more replica the output will create more cpu data in same time step 
                f.close()
        except:
            print('cant open')
        last_avg_cpu=statistics.mean(last_avg_cpu)
        return last_avg_cpu


if __name__=='__main__':
    service_name='app_mn2'
    replica=3
    print(get_cpu_utilization_from_data(service_name,replica))
    pass