from locust import HttpLocust, TaskSet, task
from faker import Faker
import random
import json

def get_user_id(client):
    r =client.get('/api/v1/user/me')
    r.raise_for_status();
    return r.json()['_id']

def list_users_folders(client, user_id):
    r = client.get('/api/v1/folder',
                name='get api.v1.folder',
                params={'parentType': 'user',
                        'parentId': user_id})
    r.raise_for_status()
    return [f['_id'] for f in r.json()]

def list_folders_in_folder(client, folder_id):
    r = client.get('/api/v1/folder',
                        name='get api.v1.folder',
                        params={'parentType': 'folder',
                                'parentId': folder_id})
    r.raise_for_status()
    return [f["_id"] for f in r.json()]

def list_items_in_folder(client, folder_id):
    r = client.get('/api/v1/item/',
                   name='get api.v1.item',
                   params={'folderId': folder_id})
    r.raise_for_status()
    return [f['_id'] for f in r.json()]

def get_random_folder_id(client, user_id, decay=0.5):
    # decay - probability of going a level deeper at any given level

    def random_folder_location(folder_id):
        if random.random() < decay:
            subfolders = list_folders_in_folder(client, folder_id)
            if not subfolders:
                return folder_id
            else:
                return random_folder_location(folder_id)
        else:
            return folder_id

    folders = list_users_folders(client, user_id)
    if not folders:
        # user has no folders
        # create folder and return folder id
        r = client.post('/api/v1/folder',
                        name='post api.v1.folder',
                        params={'parentType': 'user',
                                'parentId': user_id})
        r.raise_for_status()
        return r.json()['_id']
    return random_folder_location(folders[random.randint(0, len(folders)-1)])
