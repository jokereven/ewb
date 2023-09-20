import json
import os
import random
import time
import traceback

import requests
from dotenv import load_dotenv
from pymongo import MongoClient

class PEPE(object):

    # __init__ init connect mongo
    def __init__(self, db, collection):
        self.client = MongoClient('localhost', 27017)
        self.db = self.client[db]
        self.collection = self.db[collection]

    # @add_implementations add implementations to mongo
    def add_implementations(self, address):
        if address != None and address != '':
            result = self.collection.find_one({'address': address})

            if result:
                return True
            else:
                self.collection.insert_one({'address': address})
                return False

    # @Address check address is exist in mongo
    def Address(self, where=None):
        if where is not None:
            document = self.collection.find_one(where)
            return True if document else False
        else:
            return False

    # @Insert insert wallet address to a mongo collection
    def Insert(self, data, only_one=True):
        if only_one:
            bool = self.collection.insert_one(data)
            return bool
        else:
            bool = self.collection.insert_many(data)
            return bool

    # @get_all_address Query all addresses from mongo collection
    def get_all_address(self):
        return self.collection.find({})

    # @get_address_info Query address info from zerion api
    def get_address_info(self, address):

        url = f"https://api.zerion.io/v1/wallets/{address}/portfolio/?currency=usd"

        response = requests.get(url, headers=headers)

        time.sleep(random.random())

        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 429:
            # Request exceeding limit
            return 429
        else:
            return None

    # @is_valid_address 地址是否可用;
    def is_valid_address(self, address):

        # 根据地址查询 is_available 字段的值;
        is_available = self.collection.find_one({'address': address}).get('is_available', None)

        if is_available == None:
            info = self.get_address_info(address)

            # insert address info to mongo and update is_available
            if info != None and info != 429:
                self.collection.update_one({'address': address}, {'$set': {'is_available': True, 'info': info.get('data', {})}})
            elif info == 429:
                return 429
            else:
                self.collection.update_one({'address': address}, {'$set': {'is_available': False, 'info': {}}})

        return is_available

    # @to_float float
    def to_float(self, x):
        return round(float(x) if x is not None else 0.0, 2)

    # @get_all_trade get address trade
    def get_all_trade(self, address):

        # @tx_count Total transaction number
        tx_count = 0

        # @total_gas Total gas fee
        total_gas = 0

        # @meme_arr meme token array
        meme_arr = []

        # @token_dir token dir
        token_dir = {}

        # @token_from token from
        token_from = {}

        # usd value
        usd = 0

        # @url trade and approve
        url = f"https://api.zerion.io/v1/wallets/{address}/transactions/?currency=usd&page[size]=100&filter[operation_types]=trade&filter[asset_types]=fungible&filter[chain_ids]=ethereum"

        while True:
            try:
                print('url✅:', url)

                response = requests.get(url, headers=headers)

                time.sleep(random.random() + 0.618)

                if response.json().get("errors"):
                    break

                if response.status_code == 200:

                    # 是否需要进行下一次请求;
                    links = response.json().get("links", {})
                    next = links.get("next", {})

                    data = response.json().get("data", {})

                    for tx in data:

                        attributes = tx.get("attributes", {})
                        status = attributes.get("status", {})

                        # tx is confirmed
                        if status == "confirmed":

                            relationships = tx.get("relationships")
                            operation_type = attributes.get("operation_type", {})
                            chain_id = relationships.get("chain", {}).get("data", {}).get("id")

                            if chain_id == "ethereum" and operation_type == "trade":

                                tx_count += 1

                                fee = attributes.get("fee", {})
                                gas_value = fee.get("value", {})

                                if gas_value is not None and gas_value != {}:
                                    total_gas += self.to_float(gas_value)

                                transfers = attributes.get("transfers", {})
                                for transfer in transfers:

                                    symbol = transfer.get("fungible_info", {}).get("symbol", {})
                                    if symbol not in meme_arr and symbol != {} and symbol != None:
                                        meme_arr.append(symbol)

                                    direction = transfer.get("direction", {})
                                    numeric = transfer.get("quantity", {}).get("numeric", {})
                                    value = transfer.get("value", {})

                                    if direction == "in":

                                        if symbol in token_from:
                                            token_from[symbol] = self.to_float(token_from[symbol]) + self.to_float(numeric)
                                        else:
                                            token_from[symbol] = self.to_float(numeric)

                                        if symbol in token_dir:
                                            token_dir[symbol] = self.to_float(token_dir[symbol]) - self.to_float(value)
                                        else:
                                            token_dir[symbol] = - self.to_float(value)

                                    elif direction == "out":

                                        if symbol in token_from:
                                            token_from[symbol] = self.to_float(token_from[symbol]) - self.to_float(numeric)
                                        else:
                                            token_from[symbol] = - self.to_float(numeric)

                                        if symbol in token_dir:
                                            token_dir[symbol] = self.to_float(token_dir[symbol]) + self.to_float(value)
                                        else:
                                            token_dir[symbol] = self.to_float(value)

                    if next:
                        url = next
                    else:
                        break

            except Exception as e:
                print(f'get_all_trade failed error: {e}, please try again.')
                traceback.print_exc()
                return None

        meme_count = len(meme_arr)
        trade_equity_count = sum(1 for key in token_dir.keys() if token_dir[key] > 0 and token_from.get(key, 0) > 0)
        trade_equity = trade_equity_count / meme_count if meme_count > 0 else 0

        result = {
            "address": address,
            "usd": usd,
            "tx_count": tx_count,
            "total_gas": total_gas,
            "meme_arr": meme_arr,
            "meme_count": meme_count,
            "trade_equity_count": trade_equity_count,
            "trade_equity": trade_equity,
        }
        return result


if __name__ == '__main__':

    load_dotenv()  # 加载 .env 文件

    authorization = os.getenv('authorization')  # 获取名为 MY_VAR 的环境变量

    headers = {
        "accept": "application/json",
        "authorization": authorization
    }

    # create db connection
    pe = PEPE('gmgn', 'meme')

    addresses = pe.get_all_address()

    for i, address in enumerate(addresses):

        pepe = address['address']

        print(f"{i}: {pepe}")

        ok = pe.is_valid_address(pepe)

        print(f"ok: {ok}")

        if ok == None:

            trade = pe.get_all_trade(pepe)

            print(f"trade: {trade}")

            if trade:
                pe.collection.update_one({'address': pepe}, {'$set': {'trade': trade}})

            # 查询地址所有数据
            print(pe.collection.find_one({'address': pepe}))
        elif ok == 429:
            print('Request exceeding restrictions')
            break
        else:
            continue
