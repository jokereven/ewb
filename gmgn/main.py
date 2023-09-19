import json
import os
import random
import time
import traceback

import requests
from pymongo import MongoClient


class GMGN(object):

    # __init__ init connect mongo
    def __init__(self, db, collection):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[db]
        self.collection = self.db[collection]

    # Get all the contract address you need to request
    def gmgn(self, time: str):

        url = f'https://gmgn.ai/defi/quotation/v1/rank/eth/swaps/{time}?orderby=swaps&direction=desc'
        try:
            res = requests.get(url)
            if res.status_code == 200:
                data = json.loads(res.text)
                return data
            else:
                print('gmgn error: ', res.status_code)
                return None
        except Exception as e:
            print('gmgn failed error: ', e)
            return None

    # Update data into mongo
    def update_gmgn(self, data: list):

        for i in data:
            chain = i.get('chain', '')
            address = i.get('address', '')
            symbol = i.get('symbol', '')

            if chain and address and symbol:
                if not self.collection.find_one({'chain': chain, 'address': address, 'symbol': symbol}):
                    self.collection.insert_one(i)
                    print('insert success', 'chain: ', chain, 'address: ', address, 'symbol: ', symbol, '✅')
                else:
                    print('already exist', 'chain: ', chain, 'address: ', address, 'symbol: ', symbol, '❌')
            else:
                print('chain or address or symbol is None')

    def get_all_address(self):
        return self.collection.find({})

    def read_mongo(self, file_name: str):

        data = self.get_all_address()

        for i in data:
            chain = i.get('chain', '')
            address = i.get('address', '')
            symbol = i.get('symbol', '')

            if chain and address and symbol:

                if not os.path.exists(file_name):
                    with open(file_name, 'w') as f:
                        f.write(json.dumps({address: symbol}))
                else:
                    with open(file_name, 'r') as f:
                        try:
                            json_data = json.loads(f.read())
                        except:
                            json_data = {}
                    with open(file_name, 'w') as f:
                        if json_data.get(address):
                            if chain not in json_data.get(address):
                                json_data[address] = symbol
                        else:
                            json_data[address] = symbol
                        f.write(json.dumps(json_data))

if __name__ == '__main__':

    gmgn = GMGN('gmgn', 'gmgn')

    rank = gmgn.gmgn('24h')

    if rank:

        data = rank.get('data', {}).get('rank', [])

        gmgn.update_gmgn(data)

        gmgn.read_mongo('token.json')
