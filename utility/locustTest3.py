from locust import HttpUser, task, between
import json
import random


class WebsiteTestUser(HttpUser):
    wait_time = between(1,1)
    host = "http://host_address"

    def on_start(self):

        """ on_start is called when a Locust start before any task is scheduled """
        pass
    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        pass

    @task(1)
    def createUserConnect(self):
        path = self.host+'/simplerequest'
        data = {"mode": 'replicas3',}
        self.client.post(url=path, json=data)
        
            