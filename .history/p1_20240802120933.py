import base64
import requests
from functools import reduce
import pickle
import json
from functools import wraps
from collections import Counter, ChainMap
from itertools import chain
from operator import itemgetter

# Download data using export api


# [17:45] Karandeep Singh
# Need to create a text generation AI task by using an open source LLM. By executing the python code we should be able to talk to AI on any command shell. Preferred LLM is llama2-7b

url = "https://amplitude.com/api/2/export"
username = "9808b8a9b1dbab89368b4cea4f67a551"
password = "6cf79d385271cec8b6d3b3d940cfdde4"
params = {
    "start": "20211018T06",
    "end": "20211018T07"
}
response = requests.get(url, params=params, headers={
                        "Accept": "application/json", "Authorization": "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()})

if response.status_code == 200:
    data = response.content
    file = open('file1.zip', 'wb')
    file.write(data)
    file.close()
