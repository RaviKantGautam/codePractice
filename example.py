from typing import List
class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        count = {}
        for num in nums:
            count[num] = 1 + count.get(num, 0)
        count = filter(lambda x: x[1] >= k, sorted(count.items(), key=lambda x: x[1], reverse=True))

        arr = []
        for num, cnt in count.items():
            arr.append([cnt, num])
        print(arr)
        arr.sort()
        print(arr)

        res = []
        while len(res) < k:
            res.append(arr.pop()[1])
        return res

print(Solution().topKFrequent([1,1,1,2,2,3], 2))