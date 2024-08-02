from collections import defaultdict
import math
from typing import List


class Solution:
    def selectionSort(self, arr):
        for i in range(len(arr)):
            minIndex = i
            for j in range(i+1, len(arr)):
                if arr[j] < arr[minIndex]:
                    minIndex = j
            arr[i], arr[minIndex] = arr[minIndex], arr[i]
        return arr
    
    def bubbleSort(self, arr):
        low = 0
        high = len(arr) - 1
        while low < high:
            for i in range(low, high):
                if arr[i] > arr[i+1]:
                    arr[i], arr[i+1] = arr[i+1], arr[i]
            high -= 1
            for i in range(high, low, -1):
                if arr[i] < arr[i-1]:
                    arr[i], arr[i-1] = arr[i-1], arr[i]
            low += 1
        return arr
    
    def insertionSort(self, arr):
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and key < arr[j]:
                arr[j+1] = arr[j]
                j -= 1
            arr[j+1] = key
        return arr
    
    def merge(self, arr, low, mid, high):
        left = low
        right = mid + 1
        temp = []

        while left <= mid and right <= high:
            if arr[left] < arr[right]:
                temp.append(arr[left])
                left += 1
            else:
                temp.append(arr[right])
                right += 1

        while left <= mid:
            temp.append(arr[left])
            left += 1

        while right <= high:
            temp.append(arr[right])
            right += 1

        for i in range(low, high+1):
            arr[i] = temp[i-low]
    
    def mergeSort(self, arr, low, high):
        if low < high:
            mid = (low + high) // 2
            self.mergeSort(arr, low, mid)
            self.mergeSort(arr, mid+1, high)
            self.merge(arr, low, mid, high)
        return arr

    def partition(self, arr, low, high):
        pivot = arr[high]
        i = low-1
        for j in range(low, high):
            if arr[j] < pivot:
                i += 1
                arr[j], arr[i] = arr[i], arr[j]

        arr[i+1], arr[high] = arr[high], arr[i+1]

        return i+1

    def quickSort(self, arr, low, high):
        if low < high:
            p = self.partition(arr, low, high)
            self.quickSort(arr, low, p-1)
            self.quickSort(arr, p+1, high)

    def findUnion(self, arr1, arr2):
        i, j = 0, 0
        unionset = []

        while i < len(arr1) and j < len(arr2):
            if arr1[i] <= arr2[j]:
                if len(unionset) == 0 or unionset[-1] != arr1[i]:
                    unionset.append(arr1[i])
                i += 1
            else:
                if len(unionset) == 0 or unionset[-1] != arr2[j]:
                    unionset.append(arr2[j])
                j += 1

        while i < len(arr1):
            unionset.append(arr1[i])
            i += 1

        while j < len(arr2):
            unionset.append(arr2[j])
            j += 1

        return unionset

    def hasDuplicate(self, nums):
        '''Given an integer array nums, return true if any value appears more than once in the array, otherwise return false.'''
        hashset = set()
        for i in nums:
            if i in hashset:
                return True
            hashset.add(i)

        hashmap = {}
        for i in nums:
            hashmap[i] = i
            if i in hashmap:
                return True
        return False

    def isAnagram(self, s: str, t: str) -> bool:
        '''Given two strings s and t, return true if the two strings are anagrams of each other, otherwise return false.

        An anagram is a string that contains the exact same characters as another string, but the order of the characters can be different.
        '''
        if len(s) != len(t):
            return False
        countS, countT = {}, {}
        for i in range(len(s)):
            countS[s[i]] = 1 + countS.get(s[i], 0)
            countT[t[i]] = 1 + countT.get(t[i], 0)
        for c in countS.keys():
            if countS[c] != countT.get(c, 0):
                return False
        return True
    
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        '''
        Given an array of strings strs, group all anagrams together into sublists. You may return the output in any order.

        An anagram is a string that contains the exact same characters as another string, but the order of the characters can be different.
        '''
        hashmap = defaultdict(list)
        for s in strs:
            key = ''.join(sorted(s))
            hashmap[key].append(s)
        return hashmap.values()

    def twoSum(self, nums: List[int], target: int) -> List[int]:
        '''
        Given an array of integers nums and an integer target, return the indices i and j such that nums[i] + nums[j] == target and i != j.

        You may assume that every input has exactly one pair of indices i and j that satisfy the condition.

        Return the answer with the smaller index first.
        '''
        hashmap = {}
        for i, n in enumerate(nums):
            diff = target-n
            if diff in hashmap:
                return [hashmap[diff], i]
            hashmap[n] = i
        return
    
    def removeDuplicates(self, nums: List[int]) -> int:
        '''
        Given an integer array nums sorted in non-decreasing order, remove the duplicates in-place such that each unique element appears only once. The relative order of the elements should be kept the same.
        '''
        i = 0
        while i < len(nums) - 1:
            if nums[i] == nums[i+1]:
                nums.pop(i)
            else:
                i += 1
        return len(nums)
    
    def removeElement(self, nums: List[int], val: int) -> int:
        '''
        Given an integer array nums and an integer val, remove all occurrences of val in nums in-place. The relative order of the elements may be changed.
        '''
        i = 0
        while i < len(nums):
            if nums[i] == val:
                nums.pop(i)
            else:
                i += 1
        return len(nums)
    

    def searchInsert(self, nums: List[int], target: int) -> int:
        '''
        Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return the index where it would be if it were inserted in order.
         You must write an algorithm with O(log n) runtime complexity.

    
    Example 1:

    Input: nums = [1,3,5,6], target = 5
    Output: 2
        '''
        low, high = 0, len(nums) - 1
        while low <= high:
            mid = (low + high) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return low

    def isPalindrome(self, s: str) -> bool:
        l, r = 0, len(s)-1

        while l < r:
            while l < r and not s[l].isalnum():
                l += 1
            while r > l and not s[r].isalnum():
                r -= 1

            if s[l].lower() != s[r].lower():
                return False            
            l += 1
            r -= 1
        return True
    
    def pattern(self, s: str, t:str, case=None) -> bool:

        if case == 1:
            '''
            input_dictionary = {"a":{"b":{}},"c":{"d":{}},"e":{"f":{}}} 
            output_dictionary={"b":{"a":{}},"d":{"c":{}},"f":{"e":{}}}
            '''
            temp = {}
            for key,value in s.items():
                if isinstance(value, dict):
                    temp[list(value.keys())[0]] = {key: list(value.values())[0]}
            return temp == t
        
        elif case == 2:
            '''
            data = {
                "Amit" : "TL",
                "Ravi" : "HR",
                "Reena" : 'PM',
                "Mohan" : "TL",
                "Kapil" : "TL",
                "Rajesh" : "HR",
                "Geeta" : "TL"
            }

            output = 
                {
                    'TL': ['Amit', 'Mohan', 'Kapil', 'Geeta'],
                    'HR': ['Ravi', 'Rajesh'],
                    'PM': ['Reena']
                }
            '''
            output = {}
            for key,val in s.items():
                if val in output:
                    output[val].append(key)
                else:
                    output[val] = [key]
            return output == t
        
        elif case == 3:
            '''
            Write program to form pattern.
            For example:
            input = abbccde
            ouptut = ab2c3de
            '''
            n = len(s)
            count = 1
            output = ''

            for i in range(1, n):
                if s[i-1] == s[i]:
                    count += 1
                else:
                    if count > 1:
                        output += s[i-1]+str(count)
                    else:
                        output += s[i-1]
                    count = 1
            if count > 1:
                output += s[-1]+str(count)
            else:
                output += s[-1]
            return output == t
        

    def countDigitsWitMath(self, n):
        '''Count the number of digits in a number using math library'''
        return math.floor(math.log10(n)) + 1
    
    def countDigits(self, n):
        count = 0
        while n != 0:
            n //= 10
            count += 1
        return count
    
    def reverseNumber(self, n):
        revNum = 0
        while n != 0:
            revNum = revNum * 10 + n % 10
            n //= 10
        return revNum
    
    def findDivisors(self, n):
        divisors = []
        for i in range(1, int(n**0.5) + 1):
            if n % i == 0:
                divisors.append(i)
                if i != n // i:
                    divisors.append(n // i)
        return divisors
    
    def checkPrime(self, n):
        if n == 1:
            return False
        cnt = 0
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                cnt += 1
                if n/i != i:
                    cnt += 1
        if cnt == 2:
            return True
        return False
    
    def fibonacci(self, n):
        a, b = 0, 1
        for i in range(n):
            print(a, end=' ')
            a, b = b, a+b
    
    def fibonacciRec(self, n, a=0, b=1):
        if n == 0:
            return
        print(a, end=' ')
        self.fibonacciRec(n-1, b, a+b)

    def factorial(self, n):
        if n == 0:
            return 1
        return n * self.factorial(n-1)



if __name__ == '__main__':
    # arr1 = [1, 2, 4, 5, 6]
    # arr2 = [2, 3, 5, 7]
    # print(Solution().findUnion(arr1, arr2))

    # nums = [1, 2, 3, 1]
    # print(Solution().hasDuplicate(nums))

    # s = 'car'
    # t = 'rac'
    # print(Solution().isAnagram(s, t))

    # s='Was it a car or a cat I saw?'
    # print(Solution().isPalindrome(s))

    # s={"a":{"b":{}},"c":{"d":{}},"e":{"f":{}}}
    # t={"b":{"a":{}},"d":{"c":{}},"f":{"e":{}}}
    # print(Solution().pattern(s, t, 1))

    # s = {
    #     "Amit" : "TL",
    #     "Ravi" : "HR",
    #     "Reena" : 'PM',
    #     "Mohan" : "TL",
    #     "Kapil" : "TL",
    #     "Rajesh" : "HR",
    #     "Geeta" : "TL"
    # }
    # t = {
    #     'TL': ['Amit', 'Mohan', 'Kapil', 'Geeta'],
    #     'HR': ['Ravi', 'Rajesh'],
    #     'PM': ['Reena']
    # }

    # print(Solution().pattern(s, t, 2))

    s = 'abbcccde'
    t = 'ab2c3de'
    print(Solution().pattern(s, t, 3))
