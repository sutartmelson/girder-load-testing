from locust import HttpLocust
from powerUser import PowerUser

import loggra
loggra.setup_graphite_communication()


class MyLocust(HttpLocust):
    host = 'http://localhost:9080'
    min_wait = 3000
    max_wait = 7000
    task_set = PowerUser
