from locust import HttpLocust, TaskSet, task
from requests.auth import HTTPBasicAuth
from requests import Session
from faker import Faker
from powerUser import PowerUser
import random
import six
import tempfile
import os
import pprint
import json

BYTES_IN_MB = 1048576
MAX_CHUNK_SIZE = BYTES_IN_MB * 64
REQ_BUFFER_SIZE = 65536

# import loggra
# loggra.setup_graphite_communication()


# def _create_collection(self):
#     self.admin_session = Session()
#     r = self.admin_session.get(self.locust.host + "/api/v1/user/authentication",
#                            auth=HTTPBasicAuth('girder', 'girder'))
#     r.raise_for_status()

#     self.admin_session.headers.update({
#         'Girder-Token': r.json()['authToken']['token']
#     })
#     collection_name = self.faker.slug()

#     r = self.admin_session.post(self.locust.host + '/api/v1/collection',
#                                 params={'name': collection_name,
#                                         'public': True})
#     r.raise_for_status()


class MyLocust(HttpLocust):
    host = 'http://localhost:9080'
    min_wait = 3000
    max_wait = 7000
    task_set = PowerUser
