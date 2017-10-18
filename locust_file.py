from faker import Faker
from requests import Session
from requests.auth import HTTPBasicAuth
from locust import HttpLocust, TaskSet, task
import girder_utils
import random
import six
import tempfile
import os
import json

BYTES_IN_MB = 1048576
MAX_CHUNK_SIZE = BYTES_IN_MB * 64
REQ_BUFFER_SIZE = 65536

import loggra
# loggra.setup_graphite_communication()


class MyTaskSet(TaskSet):
    upload_file_paths = [
        # ('data/100mb.bin', 100 * BYTES_IN_MB),
        # ('data/10mb.bin', 10 * BYTES_IN_MB),
        ('data/1mb.bin', 1 * BYTES_IN_MB)
    ]
    def on_start(self):
        self.faker = Faker()
        self.create_user()
        self.login()
        self.files = []
        self.folders = []
        self.upload_file_prob = 75
        self.upload_batch_prob = 15
        self.download_prob = 10

    def create_user(self):
        admin_session = Session()
        r = admin_session.get(self.locust.host + "/api/v1/user/authentication",
                               auth=HTTPBasicAuth('girder', 'girder'))
        r.raise_for_status()

        admin_session.headers.update({
            'Girder-Token': r.json()['authToken']['token']
        })

        # create a local fake profile
        self.user_profile = self.faker.profile()
        # set the local fake profiles username
        self.user_profile['password'] = 'letmein'

        # Use the admin user to create the girder user with the local fake profile info
        r = admin_session.post(self.locust.host + "/api/v1/user", {
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

    @task(100)
    def pick_IO_task(self):
        r = random.randint(0, 100)

        if r < self.upload_file_prob:
            if self.upload_file_prob > 10:
                self.upload_file_prob -= 1
                self.download_prob += 1
            self.upload_file()
        elif r < self.upload_file_prob + self.upload_batch_prob:
            if self.upload_batch_prob > 2:
                self.upload_batch_prob -= 2
                self.download_prob += 2
            self.upload_batch()
        else:
            self.download_file()

    def upload_file(self):
        folder_id = girder_utils.get_random_folder_id(self.client, self.user_id)
        path, size = random.choice(self.upload_file_paths)
        offset = 0
        slug = self.faker.slug()

        r = self.client.post('/api/v1/file',
                             name='api.v1.folder',
                             params={
                                 'parentType': 'folder',
                                 'parentId': folder_id,
                                 'name': slug,
                                 'size': size,
                                 'mimeType': 'application/octet-stream'
                             })
        uploadObj = r.json()

        if '_id' not in uploadObj:
            raise Exception(
                'After uploading a file chunk, did not receive object with _id. '
                'Got instead: ' + json.dumps(uploadObj))


        with open(path, 'rb') as stream:
            while True:
                chunk = stream.read(min(MAX_CHUNK_SIZE, (size - offset)))

                if not chunk:
                    break

                if isinstance(chunk, six.text_type):
                    chunk = chunk.encode('utf8')

                r = self.client.post('/api/v1/file/chunk',
                                     name='post api.v1.file.chunk',
                                     params={'offset': offset, 'uploadId': uploadObj['_id']},
                                     data=chunk)
                uploadObj = r.json()

                if '_id' not in uploadObj:
                    raise Exception(
                        'After uploading a file chunk, did not receive object with _id. '
                        'Got instead: ' + json.dumps(uploadObj))

                offset += len(chunk)

        self.files.append((uploadObj['_id'], size))

    def download_file(self):
        if len(self.files) is 0:
            self.upload_file()

        file_id , size = random.choice(self.files)

        r = self.client.get('/api/v1/file/%s/download' % file_id,
                            name='api.v1.file.download',
                            stream=True)

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            for chunk in r.iter_content(chunk_size=REQ_BUFFER_SIZE):
                tmp.write(chunk)

            os.remove(tmp.name)

    def upload_batch(self):
        count = random.randint(100,5000)
        folder_id = girder_utils.get_random_folder_id(self.client, self.user_id)
        for i in range(count):
            with tempfile.NamedTemporaryFile() as temp:
                slug = self.faker.slug()
                temp.write(slug)
                temp.seek(0)
                r = self.client.post('/api/v1/file',
                         name='api.v1.file',
                         params={
                             'parentType': 'folder',
                             'parentId': folder_id,
                             'name': temp.name,
                             'size': len(slug),
                             'mimeType': 'application/text'
                         })

                uploadObj = r.json()
                if '_id' not in uploadObj:
                    raise Exception(
                        'After uploading a file chunk, did not receive object with _id. '
                        'Got instead: ' + json.dumps(uploadObj))

                r = self.client.post('/api/v1/file/chunk/',
                                     name='post api.v1.file.chunk',
                                     params={'offset': 0, 'uploadId': uploadObj['_id']},
                                     data=temp)

    @task(20)
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

        self.folders.append(r.json()['name'])

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
                             name='api.v1.resource.search',
                             params={'q': 'search_query',
                                     'mode': 'prefix',
                                     'types': json.dumps(types)})
        r.raise_for_status()

class MyLocust(HttpLocust):
    host = 'http://localhost:9080'
    min_wait = 3000
    max_wait = 7000
    task_set = MyTaskSet
