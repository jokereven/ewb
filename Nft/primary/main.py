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

    def track_rank(self):
        track_rank_mint_dir = [
            {
                'rank': True,
                'type': 'top_winner',
                'order_by': 'paired_profit_30d',
                'direction': 'desc',
                'offset': 0,
                'limit': 99
            },
            {
                'rank': False,
                'type': 'followed_popularity',
                'order_by': 'follow_count',
                'direction': 'desc',
                'offset': 0,
                'limit': 99
            },
            {
                'rank': True,
                'type': 'whale',
                'order_by': 'roi',
                'direction': 'desc',
                'offset': 0,
                'limit': 99
            },
            {
                'rank': True,
                'type': 'mint_master',
                'order_by': 'trades_7d',
                'direction': 'desc',
                'offset': 0,
                'limit': 99
            }
        ]

        for i in track_rank_mint_dir:
            self.track_rank_mint(i['rank'], i['type'], i['order_by'], i['direction'], i['offset'], i['limit'])

    def track_rank_mint(self, rank: bool, type: str, order_by: str, direction: str, offset: int, limit: int):
        rank = 'rank' if rank else ''
        url = f'https://app.nfttrack.ai/api/{rank}/{type}?order_by={order_by}&direction={direction}&offset={offset}&limit={limit}'
        print(url)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()['data']
                for i in data:
                        address = i['address']
                        ok = self.exist(address)
                        if ok:
                            continue
                        else:
                            add.insert_address(address)
        except Exception as e:
            print('track_rank_mint failed error ❌:', e, 'traceback:', traceback.format_exc())

    def nft_filp(self):
        with open('nftfilp.json', 'r') as f:
            data = json.load(f)
            for i in data['data']['list']:
                address = i['address']
                ok = self.exist(address)
                if ok:
                    continue
                else:
                    add.insert_address(address)

    def nftgo(self, address: str, index: int):
        # https://api.nftgo.io/api/v1/activity/address-specific?address=0xa86f5324129c34312187cde5b42fe283fc493fd8&limit=100&type=buy&type=mint&type=sell&tagPassiveMint=0
        url = f'https://api.nftgo.io/api/v1/activity/address-specific'
        params = {
            'address': address.lower(),
            'limit': 100,
            'type': ['mint', 'buy', 'sell'],
        }
        while True:
            try:
                if self.collection.find_one({'address': address, 'go': True}):
                    print('nftgo go ✅:', address, index)
                    break
                response = requests.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    time.sleep(random.random())
                    print('nftgo success ✅:', address, index)

                    data = response.json()['data']
                    cursor = data.get('cursor')
                    if cursor:
                        time.sleep(random.random())
                        params['cursor'] = cursor
                        print('nftgo cursor:', cursor)

                    list = data.get('list')
                    if list:
                        # Update the document in batches
                        for i in list:
                            self.update_document(address, i)
                    else:
                        self.collection.update_one({'address': address}, {'$set': {'go': True}}, upsert=True)
                        break

            except Exception as e:
                print('nftgo failed error ❌:', e, 'traceback:', 'traceback.format_exc()')
                # print('nftgo failed error ❌:', e, 'traceback:', traceback.format_exc())
                self.collection.update_one({'address': address}, {'$set': {'go': True, }}, upsert=True)
                break

    def update_document(self, address, data):
        # Add data to the 'nftgo' array in the document
        self.collection.update_one({'address': address}, {'$addToSet': {'nftgo': data}}, upsert=True)

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

    def nftgo_collection(self):
        # https://api.nftgo.io/api/v2/ranking/collections?offset=0&limit=50&by=marketCapEth&asc=-1&rarity=-1&keyword=&fields=saleNum,saleNumChange,volume,volumeEth,volumeEthChange,orderAvgPriceETH,orderAvgPriceETHChange,orderAvgPrice,orderAvgPriceChange,bestOfferPrice,bestOfferPriceChange

        offset = self.get_offset()
        limit = 1
        url = f'https://api.nftgo.io/api/v2/ranking/collections'
        params = {
            'offset': offset,
            'limit': limit,
            'by': 'marketCapEth',
            'asc': -1,
            'rarity': -1,
            'keyword': '',
            'fields': 'saleNum,saleNumChange,volume,volumeEth,volumeEthChange,orderAvgPriceETH,orderAvgPriceETHChange,orderAvgPrice,orderAvgPriceChange,bestOfferPrice,bestOfferPriceChange'
        }
        while True:
            try:
                response = requests.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    print('nftgo_collection success ✅:', params['offset'])

                    data = response.json()['data']
                    list = data.get('list')

                    for i in list:
                        cid = i['id']
                        self.nftgo_minter(cid)

                if len(list) > 0:
                    offset += limit
                    self.set_offset(offset)
                else:
                    break

            except Exception as e:
                print('nftgo_collection failed error ❌:', e, 'traceback:', traceback.format_exc())

    def nftgo_minter(self, cid: int):
        url = f'https://api.nftgo.io/api/v2/activity/collection'
        params = {
                'cid': cid,
                'limit': 100,
                'type': 'mint',
                'tagContract': '0',
            }
        while True:
            try:
                response = requests.get(url, params=params, headers=headers)
                time.sleep(random.random())
                if response.status_code == 200:
                    print('nftgo_minter success ✅:', cid)

                    data = response.json()['data']
                    list = data.get('list')

                    for i in list:
                        address = i['to']
                        ok = self.exist(address)
                        if ok:
                            continue
                        else:
                            print('nftgo_minter address insert success ✅:', address, cid)
                            add.insert_address(address)

                cursor = data.get('cursor')
                if cursor:
                    time.sleep(random.random())
                    params['cursor'] = cursor
                    print('nftgo_minter cursor:', cursor)
                else:
                    break

            except Exception as e:
                print('nftgo failed error ❌:', e, 'traceback:', traceback.format_exc())

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

if __name__ == '__main__':

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    add = EWB('nft', 'nft_track')

    # add.track_rank()

    # add.nft_filp()

    addresses = add.get_all_address()

    for i, address in enumerate(addresses):

        ewb = address['address']

        add.nftgo(ewb, i)

# 18:08 index at 34
