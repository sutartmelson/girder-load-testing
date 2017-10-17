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
        self.folders = []

    @task(1)
    def stop(self):
        self.interrupt()

    @task(10)
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

    @task(10)
    def search(self):
        search_query = self.faker.slug()
        types = ['item','folder','group','collection','user']
        r = self.client.get('/api/v1/resource/search',
                             name='api.v1.resource.search',
                             params={'q': 'search_query',
                                     'mode': 'prefix',
                                     'types': json.dumps(types)})
        r.raise_for_status()

    @task(10)
    def create_folder(self):
        folder_id = girder_utils.get_random_folder_id(self.client, self.user_id)

        folder_name = self.faker.slug()

        # Ensure slug is unique for this user
        # This is slightly over safe seeing as names only need
        # to be unique with-in each folder,  not globally per-user
        while folder_name in self.folders:
            folder_name = self.faker.slug()

        # create folder
        r = self.client.post('/api/v1/folder',
                             name='api.v1.folder',
                             params={'parentId': folder_id,
                                     'name': folder_name})
        r.raise_for_status()

        self.folders.append(r.json()['_id'])
