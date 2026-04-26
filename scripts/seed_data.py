import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
from utils.db import insert_data

with open("data/manual_data.json", "r") as f:
    dataset = json.load(f)

for record in dataset:
    res = insert_data(record)
    print("INSERT RESULT:", res)

print("✅ Data inserted")