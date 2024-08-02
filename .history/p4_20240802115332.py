def topKFrequent(nums, k):
    '''
    Given an integer array nums and an integer k, return the k most frequent elements within the array.

    The test cases are generated such that the answer is always unique.

    You may return the output in any order.
    '''
    output = list()
    for i in set(nums):
        if nums.count(i) >= k:
            output.append(i)
    return output    

# result = topKFrequent([7,7], 1) # [1,2]
# print(result)


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



# result = removeDuplicates([1,1,2]) # 2
# print(result)

def removeElement(nums, val):
    '''
    Given an integer array nums and an integer val, remove all occurrences of val in nums in-place. The order of the elements may be changed. Then return the number of elements in nums which are not equal to val.

    Consider the number of elements in nums which are not equal to val be k, to get accepted, you need to do the following things:

    Change the array nums such that the first k elements of nums contain the elements which are not equal to val. The remaining elements of nums are not important as well as the size of nums.
    Return k.
    '''
    i = 0
    while i < len(nums):
        if nums[i] == val:
            nums.pop(i)
        else:
            i+=1
    
    return len(nums)

# result = removeElement([3,2,2,3], 3) # 2
# print(result)


def searchInsert(nums, target):
    '''
    Given a sorted array of distinct integers and a target value, return the index if the target is found. If not, return the index where it would be if it were inserted in order.

    You must write an algorithm with O(log n) runtime complexity.

    
    Example 1:

    Input: nums = [1,3,5,6], target = 5
    Output: 2
    '''
    i=0
    while i < len(nums):
        if nums[i] == target or nums[i] > target:
            return i
        else:
            i+=1
    return i

# result = searchInsert([1,3,5,6], 5) # 2
# print(result)

def plusOne(digits):
    output = "".join([str(i) for i in digits])
    output = str(int(output) + 1)
    return [int(i) for i in output]
