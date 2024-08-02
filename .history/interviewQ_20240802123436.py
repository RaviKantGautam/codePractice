from collections import defaultdict
from itertools import chain    
    
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
