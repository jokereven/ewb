import json
import random
import time
import datetime
import requests
import traceback
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

    def update_index(self, index):
        if self.offset_collection.find_one({'meme': 'index'}):
            self.offset_collection.update_one({'meme': 'index'}, {'$set': {'index': index}})
        else:
            self.offset_collection.insert_one({'meme': 'index'}, {'$set': {'index': index}})

    def get_index(self):
        if self.offset_collection.find_one({'meme': 'index'}):
            return self.offset_collection.find_one({'meme': 'index'}).get('index')
        else:
            return 0

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

    add = EWB('gmgn', 'meme')
    index = EWB('gmgn', 'index')

    addresses = add.get_all_address()
    op = index.get_index()

    # fetch

    def fetch():
        for i, address in enumerate(addresses):
            ewb = address['address']
            if i >= op:
                add.nfttrack(ewb, i)
                index.update_index(i)

    fetch()

    # 一级
    def minter():
        for i, eth in enumerate(addresses):
            ewb = eth['address']
            data = eth.get('data', {})

            roi = data.get('roi', 0)
            win_rate = data.get('win_rate', 0)

            last_active_timestamp = data.get('last_active_timestamp', 0)
            one_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%s")
            txs_7d = data.get('txs_7d', 0)

            nft_count = data.get('nft_count', 0)
            adjusted_nft_count = data.get('adjusted_nft_count', 0)

            win_sales = data.get('win_sales', 0)

            # bluechip or whale
            is_bluechip_owner = data.get('is_bluechip_owner', False)
            is_whale = data.get('is_whale', False)

            # 1. 七天有交易
            # 2. 胜率高
            # 3. 回报率高

            # time
            if txs_7d is not None and txs_7d <= 0:
                continue

            elif last_active_timestamp is not None and int(last_active_timestamp) < int( one_week):
                continue


            # win_rate
            elif win_rate is not None and win_rate < 0.95:
                continue

            # roi
            elif roi is not None and roi < 2.5:
                continue

            # all nft count
            elif nft_count is not None and nft_count > 100:
                continue

            # win sales
            elif win_sales is not None and win_sales < 28:
                continue

            with open('minter.txt', 'a') as f:
                f.write(f'{ewb}\n')

    # 二级
    def bs():
        print

minter()

# TODO 找到一级二级地址
