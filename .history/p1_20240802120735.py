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


class Solution:
    '''
    Write a function to find the longest common prefix string amongst an array of strings.

    If there is no common prefix, return an empty string "".



    Example 1:

    Input: strs = ["flower","flow","flight"]
    Output: "fl"
    Example 2:

    Input: strs = ["dog","racecar","car"]
    Output: ""
    Explanation: There is no common prefix among the input strings.

    '''

    def longestCommonPrefix(self, strs):
        largest_word = min(strs, key=len)
        common_prefix = ""
        for i in range(len(largest_word)):
            flag = False
            for word in strs:
                if largest_word[i] == word[i]:
                    flag = True
                else:
                    flag = False
                    break
            if flag == True:
                common_prefix += largest_word[i]
            else:
                break

        return common_prefix

