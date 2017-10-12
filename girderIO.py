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


    @task(1)
    def stop(self):
        self.interrupt()

    @task(10)
    def upload_file(self):
        folder_id = girder_utils.get_random_folder_id(self.client, self.user_id)
        path, size = random.choice(self.upload_file_paths)
        offset = 0
        slug = self.faker.slug()

        r = self.client.post('/api/v1/file',
                             # name='/api/v1/file, %s, %s, %s, %s' % (size, offset, folder_id, slug))
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

    @task(10)
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

    @task(10)
    def upload_batch(self):
        count = random.randint(100,5000)
        folder_id = girder_utils.get_random_folder_id(self.client, self.user_id)
        with tempfile.NamedTemporaryFile(mode='w') as temp:
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
