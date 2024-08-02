# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def mergeTwoLists(self, list1, list2):
        n1 = list1.next
        while not n1:
            print(n1.val)
            n1 = list1.next

result = Solution()
result.mergeTwoLists([1,2,4], )

        