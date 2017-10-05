from locust import HttpLocust
from powerUser import PowerUser



class MyLocust(HttpLocust):
    host = 'http://localhost:9080'
    min_wait = 3000
    max_wait = 7000
    task_set = PowerUser
