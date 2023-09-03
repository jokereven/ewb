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

    def nftgo(self, address: str):
        # https://api.nftgo.io/api/v1/activity/address-specific?address=0xa86f5324129c34312187cde5b42fe283fc493fd8&limit=100&type=buy&type=mint&type=sell&tagPassiveMint=0
        url = f'https://api.nftgo.io/api/v1/activity/address-specific'
        params = {
            'address': address.lower(),
            'limit': 100,
            'type': ['mint', 'buy', 'sell'],
        }
        while True:
            try:
                response = requests.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    print('nftgo success ✅:', address)

                    data = response.json()['data']
                    list = data.get('list')

                    for i in list:
                        self.collection.update_one({'address': address}, {'$addToSet': {'nftgo': i}}, upsert=True)

                cursor = data.get('cursor')
                if cursor:
                    time.sleep(random.random())
                    params['cursor'] = cursor
                    print('cursor:', cursor)
                else:
                    break

            except Exception as e:
                print('nftgo failed error ❌:', e, 'traceback:', traceback.format_exc())

    def get_offset(self):
        offset_doc = self.offset_collection.find_one()
        if offset_doc:
            print('offset_doc:', offset_doc)
            time.sleep(random.random())
            return offset_doc['offset']
        else:
            return 0

    def set_offset(self, offset):
        print('offset:', offset)
        self.offset_collection.update_one({}, {'$set': {'offset': offset}}, upsert=True)

    def exist(self, address):
        query = {'address': address}
        result = self.collection.find_one(query)
        if result:
            print('address exist ❌:', address)
            return True
        else:
            return False

    def get_all_address(self):
        return self.collection.find({})

    def insert_address(self, address):
        data = {
            'address': address,
        }
        print('address insert success ✅:', address)
        self.collection.insert_one(data)

    def freemint(self):
        with open('meme.json', 'r') as f:
            addresss = json.load(f)[0]
            for address in addresss:
                if self.exist(address['address']):
                    continue
                self.insert_address(address['address'])

if __name__ == '__main__':

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    add = EWB('ewb', 'freemint')

    add.freemint()

    addresses = add.get_all_address()

    for i, address in enumerate(addresses):

        ewb = address['address']

        add.nftgo(ewb)
