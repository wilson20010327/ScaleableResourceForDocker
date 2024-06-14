import matplotlib.pyplot as plt
x=[]
count=0
with open("request.txt", "r") as f:
    while(1):
        x.append(int(f.readline()))
        count+=1
        if (count>=4000):
            break
plt.plot(x)
plt.show()