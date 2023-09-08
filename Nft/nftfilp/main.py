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

    def get_all_address(self):
        return self.collection.find({})

    def nfttrack(self, address, i):
        url = f'https://app.nfttrack.ai/api/address_info/{address}'
        if self.collection.find_one({'address': address}).get('nfttrack'):
            print(f'[{i}] {address} exists', '❌')
            return
        response = requests.get(url, headers=headers)
        time.sleep(random.random())
        if response.status_code == 200:
            code = response.json()['code']
            msg = response.json()['msg']
            if code == 0 and msg == 'success':
                data = response.json()['data']
                self.collection.update_one({'address': address}, {'$set': {'data': data}})
                self.collection.update_one({'address': address}, {'$set': {'nfttrack': True}})
                print(f'[{i}] {address} {code} {msg}', '✅')
            else:
                print(f'[{i}] {address} {code} {msg}', '❌')

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
