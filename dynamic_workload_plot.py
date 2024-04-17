import numpy as np
import matplotlib.pyplot as plt
import math,random
def fluctuate_function_sin(prev,x, mean, max_value, min_value,func_num):
    x=int(x/5)
    temp=0
    # for i in range(func_num):
    #     temp+=mean + (max_value - min_value) / 2 * math.sin((i+1)*x)
    # temp/=func_num
    temp=min_value + (max_value - min_value)*random.random()
    if (prev==0):
        prev=temp
        return temp
    else:
        return prev
mean_value = 50
max_limit = 160
min_limit = 5
temp= [i for i in range(1,3630)]
# Generate x values


# Calculate y values using the fluctuate_function_sin
y_values_sin = []
prev=0  
def fluctuate_function_sin(prev,x, mean=mean_value, max_value=max_limit, min_value=min_limit,func_num=5):
    x=int(x/5)
    temp=0
    # for i in range(func_num):
    #     temp+=mean + (max_value - min_value) / 2 * math.sin((i+1)*x)
    # temp/=func_num
    temp=min_value + (max_value - min_value)*random.random()
    if (prev==0):
        return temp
    else:
        # print("get")
        return prev

for timestamp in range(1,3630+1):
    if timestamp % 30 ==0 :
        if timestamp == (3630):
            done = True
        prev=0      
    # get the cpu usage from docker stats too slow need to use thread
    if timestamp % 30 >= 30-5:
        
        request_num=mean_value
        prev=request_num=int(fluctuate_function_sin(prev,int(timestamp/30)))
        y_values_sin.append(request_num)

x_plot=[i for i in range(len(y_values_sin))]
# print(x_plot,y_values_sin)
# Plot the function
plt.plot(x_plot, y_values_sin)
plt.title('Fluctuating Function using Sin: mean={}, max={}, min={}'.format(mean_value, max_limit, min_limit))
plt.xlabel('x')
plt.ylabel('f(x)')
plt.show()