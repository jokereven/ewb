import json
import random
import time
import traceback
import requests
from pymongo import MongoClient

class EWB(object):

    def __init__(self, db, collection):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[db]
        self.collection = self.db[collection]
        self.offset_collection = self.db['offset']
        self.session = requests.Session()  # Create a session for making HTTP requests

    def get_all_address(self):
        return self.collection.find({})

    def nfttrack(self, address, i):
        url = f'https://app.nfttrack.ai/api/address_info/{address}'
        if self.collection.find_one({'address': address}).get('nfttrack'):
            print(f'[{i}] {address} exists', '❌')
            return
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception if the request was not successful
            time.sleep(random.random())
            data = response.json().get('data')
            if data:
                self.collection.update_one({'address': address}, {'$set': {'data': data, 'nfttrack': True}})
                print(f'[{i}] {address} Success', '✅')
            else:
                print(f'[{i}] {address} No data found', '❌')
        except requests.exceptions.RequestException as e:
            print(f'[{i}] {address} Request Error:', e)

if __name__ == '__main__':
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    add = EWB('fun', 'meme')

    addresses = add.get_all_address()

    for i, address in enumerate(addresses):
        ewb = address['address']
        add.nfttrack(ewb, i)
