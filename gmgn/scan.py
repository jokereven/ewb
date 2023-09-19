import json
import os

import requests
from pymongo import MongoClient


class PEPE(object):

    # init db and collection
    def __init__(self, db, collection):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[db]
        self.collection = self.db[collection]

    # check address is exist
    def Address(self, where=None):
        if where is not None:
            document = self.collection.find_one(where)
            return True if document else False
        else:
            return False

    # insert data to collection
    def Insert(self, data, only_one=True):
        if only_one:
            bool = self.collection.insert_one(data)
            return bool
        else:
            bool = self.collection.insert_many(data)
            return bool

    # find all address
    def get_all_address(self):
        return self.collection.find({})

    # get address trade
    def get_all_trade(self, address):

        headers = {
            "accept": "application/json",
            "authorization": "Basic emtfZGV2XzI4NTMxMWNiZTQ3NDQ0ZTBhMzY1ODMzYTEzNGQ2ODczOg=="
        }

        # now only to analysis ethereum chain
        url = "https://api.zerion.io/v1/wallets/" + address.lower() + "/transactions/?currency=eth&page[size]=100&filter[chain_ids]=ethereum"

        while True:
            try:
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    print(response.json())

            except Exception as e:
                print(f'get_all_trade failed error: {e}')
                return None


if __name__ == '__main__':

    directory = 'scan/token'

    # create db connection
    pe = PEPE('gmgn', 'DEADMIGOS')

    file_count = len(os.listdir(directory))
    start_file = 0 # set the starting file number here
    current_file = 0
    line_count = 0
    for i, filename in enumerate(os.listdir(directory)):
        if filename.endswith('.json'):
            current_file += 1
            if current_file <= start_file:
                continue
            with open(os.path.join(directory, filename), 'r') as f:
                data = json.load(f)
                keys = list(data)

                for address in keys:
                    res = pe.Address(where={'address': address})

                    if res == False:
                        data = {'address': address}

                        pe.Insert(data, only_one=True)
                        line_count += 1
                        print(f"insert address success ✅: {address} schedule: {i+1} / {file_count} Total lines read: {line_count}")
                    else:
                        print(f"address always exist ❌: {address} schedule: {i+1} / {file_count} Total lines read: {line_count}")
