from locust import HttpLocust, TaskSet, task
from requests import Session
from faker import Faker
import girder_utils
import random
import json


class NavigateGirder(TaskSet):

    def on_start(self):
        self.user_id = girder_utils.get_user_id(self.client)
        self.faker = Faker()

    @task(1)
    def stop(self):
        self.interrupt()

    @task(50)
    def randomly_navigate_user_folders(self):
        folders = girder_utils.list_users_folders(self.client, self.user_id)

        def explore(folders, decay=0.8):
            # decay - likelyhood if traversing a level deeper at any given level
            if not folders:
                return 'leaf'
            folders = random.shuffle(folders)
            for folder_id in folders:
                if random.random() < decay:
                    folders = girder_utils.list_folders_in_folder(self.client, folder_id)
                    if explore(folders) == 'leaf':
                        girder_utils.list_items_in_folder(self.client, folder_id)

    @task(50)
    def search(self):
        search_query = self.faker.slug()
        types = ['item','folder','group','collection','user']
        r = self.client.get('/api/v1/resource/search',
                             name='post api.v1.resource.search',
                             params={'q': 'search_query',
                                     'mode': 'prefix',
                                     'types': json.dumps(types)})
        r.raise_for_status()
