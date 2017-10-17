from locust import HttpLocust, TaskSet, task
from faker import Faker
import girder_utils
import random
import six
import tempfile
import os
import json

BYTES_IN_MB = 1048576
MAX_CHUNK_SIZE = BYTES_IN_MB * 64
REQ_BUFFER_SIZE = 65536


class GirderIO(TaskSet):
    upload_file_paths = [
        # ('data/100mb.bin', 100 * BYTES_IN_MB),
        # ('data/10mb.bin', 10 * BYTES_IN_MB),
        ('data/1mb.bin', 1 * BYTES_IN_MB)
    ]
    def on_start(self):
        self.faker = Faker()
        self.user_id = girder_utils.get_user_id(self.client)
        self.files = []
        self.folders = []
        self.upload_file_prob = 75
        self.upload_batch_prob = 15
        self.download_prob = 10

    @task(1)
    def stop(self):
        self.interrupt()

    @task(100)
    def pick_task(self):
        r = random.randint(0, 100)

        if r < self.upload_file_prob:
            if self.upload_file_prob > 10:
                self.upload_file_prob -= 1
                self.download_prob += 1
            print('Upload prob', self.upload_file_prob)
            self.upload_file()
        elif r < self.upload_file_prob + self.upload_batch_prob:
            if self.upload_batch_prob > 10:
                self.upload_batch_prob -= 1
                self.download_prob += 1
            print('Upload batch prob', self.upload_batch_prob)
            self.upload_batch()
        else:
            print('Download prob', self.download_prob)
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
                                     name='api.v1.file.chunk',
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
                                     name='api.v1.file.chunk',
                                     params={'offset': 0, 'uploadId': uploadObj['_id']},
                                     data=temp)

    @task(0)
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

