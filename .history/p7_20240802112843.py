from collections import defaultdict
from typing import List


class Solution:
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

    def twoSum(self, nums: List[int], target: int) -> List[int]:
        hashmap = {}
        for i, n in enumerate(nums):
            diff = target-n
            if diff in hashmap:
                return [hashmap[diff], i]
            hashmap[n] = i
        return

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


if __name__ == '__main__':
    # arr1 = [1, 2, 4, 5, 6]
    # arr2 = [2, 3, 5, 7]
    # print(Solution().findUnion(arr1, arr2))

    # nums = [1, 2, 3, 1]
    # print(Solution().hasDuplicate(nums))

    # s = 'car'
    # t = 'rac'
    # print(Solution().isAnagram(s, t))

    s='Was it a car or a cat I saw?'
    print(Solution().isPalindrome(s))
