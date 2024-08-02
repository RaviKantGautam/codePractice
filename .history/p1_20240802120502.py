import base64
import requests
from functools import reduce
import pickle
import json
from functools import wraps
from collections import Counter, ChainMap
from itertools import chain
from operator import itemgetter

# Example:
# Input: "+911234567890"
# Output: Country code:+91, Mobile number:1234567890

# Input: "+11234567890"
# Output: Country code:+1, Mobile number:1234567890


# def get_country_code_and_mobile_number(phone_number):
#     if phone_number[0] == '+':
#         country_code = phone_number[0:len(phone_number)-10]
#         mobile_number = phone_number[-10:]
#     return f"Country code:{country_code}, Mobile number:{mobile_number}"

# print(get_country_code_and_mobile_number("+911234567890"))


# Expression = "[{(){}}]" :  Valid
# Expression = "[{}}]" :  Invalid
# Expression = "[(])" :  Invalid

# --------------------------------------------------------------------------------------------

# def is_valid_expression(expression):
#     stack = []
#     opening_brackets = ['[', '(', '{']
#     closing_brackets = [']', ')', '}']

#     for char in expression:
#         if char in opening_brackets:
#             stack.append(char)
#         elif char in closing_brackets:
#             if not stack:
#                 return False
#             last_opening_bracket = stack.pop()
#             if opening_brackets.index(last_opening_bracket) != closing_brackets.index(char):
#                 return False

#     return len(stack) == 0

# expression = "[(])"
# if is_valid_expression(expression):
#     print(f"The expression '{expression}' is valid.")
# else:
#     print(f"The expression '{expression}' is invalid.")

# ---------------------------------------------------------------------------


# input_lt = [10, 5, 6, 3, 2, 20, 100, 80]
# we need to sort the output in form  of wave
def wave_sort(lst):
    # Sort the list first
    lst.sort()

    # Swap adjacent elements
    for i in range(0, len(lst) - 1, 2):
        lst[i], lst[i+1] = lst[i+1], lst[i]

    return lst


# Example usage
input_lt = [10, 5, 6, 3, 2, 20, 100, 80]
wave_sorted_list = wave_sort(input_lt)
print(wave_sorted_list)


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


class Solution:
    def romanToInt(self, s: str) -> int:
        roman_values = {
            'I': 1,
            'V': 5,
            'X': 10,
            'L': 50,
            'C': 100,
            'D': 500,
            'M': 1000
        }

        total = 0
        n = len(s)

        for i in range(n):
            if i < n - 1 and roman_values[s[i]] < roman_values[s[i + 1]]:
                total -= roman_values[s[i]]
            else:
                total += roman_values[s[i]]

        return total
