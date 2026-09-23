from typing import List
from typing import Optional

# class Solution:
#     def vowelStrings(self, word: str, queries: List[List[int]]) -> List[int]:
#         # Your code goes here
#         vowel_set = set('aeiou')
#         output = []
#         for i in queries:
#             char_set = set(word[i[0]:i[1]+1])
#             output.append(len(vowel_set.intersection(char_set)))
#         return output

# if __name__ == "__main__":
#     solution = Solution()
#     word = "prefixsum"
#     queries = [[0, 2], [1, 4], [3, 5]]
#     print(solution.vowelStrings(word, queries))

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

# class Solution:
#     def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
#         merged_list = ListNode()
#         current = merged_list

#         while list1 and list2:
#             if list1.val < list2.val:
#                 current.next = list1
#                 list1 = list1.next
#             else:
#                 current.next = list2
#                 list2 = list2.next
#             current = current.next

#         current.next = list1 or list2
#         return merged_list.next

# if __name__ == "__main__":
#     solution = Solution()
#     # Example usage:
#     # Input: list1 = [1,2,4], list2 = [1,3,5]

#     # Output: [1,1,2,3,4,5]
#     list1 = ListNode(1, ListNode(2, ListNode(4)))
#     list2 = ListNode(1, ListNode(3, ListNode(5)))
#     merged = solution.mergeTwoLists(list1, list2)
#     while merged:
#         print(merged.val, end=" -> ")
#         merged = merged.next
#     print("None")


# class Solution:
#     def numUniqueEmails(self, emails: List[str]) -> int:
#         send = set()
#         for email in emails:
#             local, domain = email.split("@")
#             local = local.split("+")[0]
#             local = local.replace(".", "")
#             send.add(f"{local}@{domain}")
#         return len(send)

# if __name__ == "__main__":
#     solution = Solution()
#     emails = ["test.email+alex@leetcode.com", "test.e.mail+bob.cathy@leetcode.com", "testemail+david@lee.tcode.com"]
#     print(solution.numUniqueEmails(emails))

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

# class Solution:    
#     def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
#         lst = []
#         head = ListNode()

#         for lt in lists:
#             current = lt
#             while current:
#                 lst.append(current.val)
#                 current = current.next
#         lst = sorted(lst)
#         dummy = head
#         for i in lst:
#             dummy.next = ListNode(i)
#             dummy = dummy.next
#         return head.next

# if __name__ == "__main__":
#     solution = Solution()
#     # Example usage:
#     # Input: lists = [[1,4,5],[1,3,4],[2,6]]
#     list1 = ListNode(1, ListNode(4, ListNode(5)))
#     list2 = ListNode(1, ListNode(3, ListNode(4)))
#     list3 = ListNode(2, ListNode(6))
#     lists = [list1, list2, list3]
#     merged = solution.mergeKLists(lists)
#     while merged:
#         print(merged.val, end=" -> ")
#         merged = merged.next
#     print("None")