from collections import defaultdict
from itertools import chain    
    
class Solution:
    '''
    Design an algorithm to encode a list of strings to a single string. The encoded string is then decoded back to the original list of strings.

    Please implement encode and decode
    '''

    def encode(self, strs) -> str:
        res = ""
        for s in strs:
            res += str(len(s)) + "#" + s
        return res

    def decode(self, s: str):
        res = []
        i = 0
        
        while i < len(s):
            j = i
            while s[j] != '#':
                j += 1
            length = int(s[i:j])
            i = j + 1
            j = i + length
            res.append(s[i:j])
            i = j
            
        return res
    
# s = Solution()
# result = s.encode(["neet","code","love","you"]) # "x"
# print(result)
# result = s.decode(result) # ["neet","code","love","you"]
# print(result)

def frequencySort(nums):
    '''
    Given an array of integers nums, sort the array in increasing order based on the frequency of the values. If multiple values have the same frequency, sort them in decreasing order.

    Return the sorted array.
    

    Example 1:

    Input: nums = [1,1,2,2,2,3]
    Output: [3,1,1,2,2,2]
    Explanation: '3' has a frequency of 1, '1' has a frequency of 2, and '2' has a frequency of 3.
    '''
    # Step 1: Count the frequency of each number
    freq_dict = {}
    for num in nums:
        freq_dict[num] = freq_dict.get(num, 0) + 1
    
    # Step 2: Sort the numbers by frequency first, and by number value if frequencies are the same
    sorted_nums = sorted(nums, key=lambda x: (freq_dict[x], -x))
    
    return sorted_nums


def getConcatenation(nums):
    '''
    Given an integer array nums of length n, you want to create an array ans of length 2n where ans[i] == nums[i] and ans[i + n] == nums[i] for 0 <= i < n (0-indexed).

    Specifically, ans is the concatenation of two nums arrays.

    Return the array ans.

    

    Example 1:

    Input: nums = [1,2,1]
    Output: [1,2,1,1,2,1]
    Explanation: The array ans is formed as follows:
    - ans = [nums[0],nums[1],nums[2],nums[0],nums[1],nums[2]]
    - ans = [1,2,1,1,2,1]
    '''
    return nums + nums

def allAnagram(s1, s2):
    '''
    Given two strings s1 and s2, return true if s2 contains the permutation of s1.

    In other words, one of s1's permutations is the substring of s2.
    '''
    return sorted(s1) in [sorted(s2[i:i+len(s1)]) for i in range(len(s2)-len(s1)+1)]


def hammingWeight(n):
    '''
    Write a function that takes an unsigned integer and returns the number of '1' bits it has (also known as the Hamming weight).
    
    res = 0
    while n:
        res += n & 1
        n >>= 1
    return res
    '''
    return bin(n).count('1')


def countBits(n):
    '''
    Given an integer n, return an array ans of length n + 1 such that for each i (0 <= i <= n), ans[i] is the number of 1's in the binary representation of i.
    
    dp = [0] * (n+1)
    offset = 1

    for i in range(1, n+1):
        if offset * 2 == i:
            offset *= 2
        dp[i] = dp[i - offset] + 1
    return dp
    '''
    return [bin(i).count('1') for i in range(n+1)]


def reverseBits(n):
    '''
    Reverse bits of a given 32 bits unsigned integer.
    res = 0
    for i in range(32):
        bit = (n >> i) & 1
        res += (bit << (31 - i))
    return res
    '''
    return int(bin(n)[2:].zfill(32)[::-1], 2)

def getSum(a, b):
    '''
    Calculate the sum of two integers a and b, but you are not allowed to use the operator + and -.
    '''
    
    while b:
        a, b = a ^ b, (a & b) << 1
    return a
