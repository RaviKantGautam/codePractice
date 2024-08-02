def countAlpha(raw_string):
    '''
    Write program to form pattern.
    For example:
    input = abbccde
    ouptut = ab2c3de
    '''
    n = len(raw_string)
    count = 1
    output = ''

    for i in range(1, n):
        if raw_string[i-1] == raw_string[i]:
            count += 1
        else:
            output += raw_string[i-1]+str(count)
            count = 1
    if count > 1:
        output += raw_string[-1]+str(count)
    else:
        output += raw_string[-1]
    return output


def waveSort(pattern):
    '''
    WAP to sort the list in ascending order and output the result in wave format.
    input = asdfhjkl
    output = dahfkjsl
    '''
    pattern = list(pattern)
    pattern.sort()
    n=len(pattern)

    for i in range(0,n-1,2):
        pattern[i], pattern[i+1] = pattern[i+1], pattern[i]
    
    pattern = "".join(pattern)
    return pattern

def validateBracket(pattern):
    '''
    WAP to check that the all the open brackets are also closed.
    input = [{()}]
    output = True
    '''
    open_bracket = ['[','{','(']
    close_bracket = [']','}',')']
    stack = []

    for char in pattern:
        if char in open_bracket:
            stack.append(char)
        elif char in close_bracket:
            if not stack:
                return False
            last_open_bracket = stack.pop()
            if open_bracket.index(last_open_bracket) != close_bracket.index(char):
                return False
        
    return len(stack) == 0


def romanToInt(s):
    '''
    Roman numerals are represented by seven different symbols: I, V, X, L, C, D and M.

    Symbol       Value
    I             1
    V             5
    X             10
    L             50
    C             100
    D             500
    M             1000
    For example, 2 is written as II in Roman numeral, just two ones added together. 12 is written as XII, which is simply X + II. The number 27 is written as XXVII, which is XX + V + II.

    Roman numerals are usually written largest to smallest from left to right. However, the numeral for four is not IIII. Instead, the number four is written as IV. Because the one is before the five we subtract it making four. The same principle applies to the number nine, which is written as IX. There are six instances where subtraction is used:

    I can be placed before V (5) and X (10) to make 4 and 9. 
    X can be placed before L (50) and C (100) to make 40 and 90. 
    C can be placed before D (500) and M (1000) to make 400 and 900.
    Given a roman numeral, convert it to an integer.

    

    Example 1:

    Input: s = "III"
    Output: 3
    Explanation: III = 3.
    '''
    valid_roman = {
        'I':1,
        'V':5,
        'X':10,
        'L':50,
        'C':100,
        'D':500,
        'M':1000
    }
    n = len(s)
    total = 0

    for i in range(0,n):
        if i < n-1 and valid_roman[s[i]] < valid_roman[s[i+1]]:
            total -= valid_roman[s[i]]
        else:
            total += valid_roman[s[i]]
    
    return total


def longestCommonPrefix(strs):
    '''
    Write a function to find the longest common prefix string amongst an array of strings.

    If there is no common prefix, return an empty string "".

    

    Example 1:

    Input: strs = ["flower","flow","flight"]
    Output: "fl"

    '''
    i = 0
    result = ""
    while i < len(strs[0]):
        char = strs[0][i]
        for j in range(1, len(strs)):
            if i >= len(strs[j]) or strs[j][i] != char:
                return result
        result += char
        i += 1
    return result


def twoSum(nums, target):
    '''
    Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

    You may assume that each input would have exactly one solution, and you may not use the same element twice.

    You can return the answer in any order.

    

    Example 1:

    Input: nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
    '''
    n = len(nums)
    for i in range(0,n):
        for j in range(i+1,n):
            if target == nums[i] + nums[j]:
                return [i,j]
    return []


def BinarySearch(nums, target):
    '''
    Given an array of integers nums which is sorted in ascending order, and an integer target, write a function to search target in nums. If target exists, then return its index. Otherwise, return -1.

    You must write an algorithm with O(log n) runtime complexity.
    

    Example 1:

    Input: nums = [-1,0,3,5,9,12], target = 9
    Output: 4
    Explanation: 9 exists in nums and its index is 4
    '''
    low = 0
    high = len(nums)-1

    while low <= high:
        mid = low + (high - low)//2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            low = mid + 1
        else:
            high = mid -1
    return -1

def moveZeroes(nums):
    '''
    Given an integer array nums, move all 0's to the end of it while maintaining the relative order of the non-zero elements.

    Note that you must do this in-place without making a copy of the array.
    Example 1:

    Input: nums = [0,1,0,3,12]
    Output: [1,3,12,0,0]
    
    '''

    left = 0
    for right in range(len(nums)):
        if nums[right] != 0:
            nums[left], nums[right] = nums[right], nums[left]
            left += 1


def majorityElement(nums):
    '''
    Given an array nums of size n, return the majority element.

    The majority element is the element that appears more than ⌊n / 2⌋ times. You may assume that the majority element always exists in the array.

    

    Example 1:

    Input: nums = [3,2,3]
    Output: 3
    '''

    max_val = {}
    for i in set(nums):
        if not max_val:
            max_val[i] = nums.count(i)
            key = i
            continue
        if nums.count(i) > max(list(max_val.values())):
            max_val[i] = nums.count(i)
            key = i
    return key


def singleNumber(nums):
    for i in set(nums):
        if nums.count(i) == 1:
            return i


def maxProfit(prices):
    '''
    You are given an array prices where prices[i] is the price of a given stock on the ith day.

    You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.

    Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return 0.

    

    Example 1:

    Input: prices = [7,1,5,3,6,4]
    Output: 5
    Explanation: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.
    Note that buying on day 2 and selling on day 1 is not allowed because you must buy before you sell.
    '''
    max_profit = 0
    count = 0
    next_counter = 1
    while next_counter < len(prices):
        low = prices[count]
        next_max_val = prices[next_counter]
        if low < next_max_val:
            profit = next_max_val - low
            max_profit = max(profit,max_profit)
        else:
            count = next_counter
        next_counter+=1

    return max_profit


def searchInsert(nums, target):
    '''
    Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return the index where it would be if it were inserted in order.

    You must write an algorithm with O(log n) runtime complexity.

    

    Example 1:

    Input: nums = [1,3,5,6], target = 5
    Output: 2
    '''
    count = 0
    while count < len(nums):
        if nums[count] == target or target < nums[count]:
            return count
        count+=1
    return count


def pascalTrigle(numRows):
    res = [[1]]
    
    for _ in range(numRows - 1):
        dummy_row = [0] + res[-1] + [0]
        row = []

        for i in range(len(res[-1]) + 1):
            row.append(dummy_row[i] + dummy_row[i+1])
        res.append(row)
    
    return res
    
    
def add_without_arithmetic_operators(a, b):
    while b != 0:
        carry = a & b
        a = a ^ b
        b = carry << 1
    return a


def missingNumber(nums):
    '''
    Given an array nums containing n integers in the range [0, n] without any duplicates, return the single number in the range that is missing from nums.

    Follow-up: Could you implement a solution using only O(1) extra space complexity and O(n) runtime complexity?

    Example 1:
    Input: nums = [1,2,3]

    Output: 0
    '''
    ct = len(nums)        
    return ((ct*(ct+1))//2) - sum(nums)


def reverse_number(num):
    ''' Q Reverse the interger number '''
    num2 = 0
    while num > 0:
        temp = num % 10
        num2 = num2 * 10 + temp
        num = num // 10
    return num2

def factorial(n):
    ''' Write factorial program using recursion '''
    return 1 if n <= 1 else n * factorial(n-1)


def get_prime():
    ''' Q write get all prime number from the list using lambda function '''
    return list(filter(lambda x: all(x % y != 0 for y in range(2, x)), range(2, 25)))
