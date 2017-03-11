import argparse

from tinydb import TinyDB, where, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

import json
import os
import io

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='raw_json', default='data/raw_dict.json')
    parser.add_argument('-d', '--dest', dest='tinydb_json', default='data/user_data.json')
    
    args = parser.parse_args()
    db = TinyDB(args.tinydb_json, storage=CachingMiddleware(JSONStorage))
    f = open(args.raw_json)
    with f as data_file:
        raw_data = json.load(data_file)
        f.close()

    db.insert_multiple(raw_data)
    db.close()
