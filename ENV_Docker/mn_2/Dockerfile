FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python && apt-get install -y python3-pip
RUN apt install stress-ng -y
RUN pip install flask
COPY . .
# CMD ["pip", "install","flask"] 
CMD ["/bin/bash", "-c","python3 server.py"] 
