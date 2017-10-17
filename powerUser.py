from locust import HttpLocust, TaskSet, task
from faker import Faker
from requests import Session
from requests.auth import HTTPBasicAuth
from girderIO import GirderIO
from navigateGirder import NavigateGirder
import girder_utils
import random
import json

class PowerUser(TaskSet):

    tasks = {GirderIO: 4, NavigateGirder: 3}

    def on_start(self):
        self.faker = Faker()
        self.create_user()
        self.login()

    def create_user(self):
        self.admin_session = Session()
        r = self.admin_session.get(self.locust.host + "/api/v1/user/authentication",
                               auth=HTTPBasicAuth('girder', 'girder'))
        r.raise_for_status()

        self.admin_session.headers.update({
            'Girder-Token': r.json()['authToken']['token']
        })

        # create a local fake profile
        self.user_profile = self.faker.profile()
        # set the local fake profiles username
        self.user_profile['password'] = 'letmein'

        # Use the admin user to create the girder user with the local fake profile info
        r = self.admin_session.post(self.locust.host + "/api/v1/user", {
            "login": self.user_profile['username'],
            "email": self.user_profile['mail'],
            "firstName": self.user_profile['name'].split(" ")[0],
            "lastName": self.user_profile['name'].split(" ")[1],
            "password": self.user_profile['password'],
            "admin": False
        })
        r.raise_for_status()
        # Set the user_id locally
        self.user_id = r.json()['_id']

    def login(self):
        # Login as the user
        r = self.client.get("/api/v1/user/authentication",
                            auth=HTTPBasicAuth(self.user_profile['username'],
                                               self.user_profile['password']))
        r.raise_for_status()

        self.client.headers.update({
            'Girder-Token': r.json()['authToken']['token']
        })
