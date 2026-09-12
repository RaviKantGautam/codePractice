class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

def create_linked_list(arr):
    head = None
    for i in range(len(arr)):
        new_node = Node(arr[i])
        if head is None:
            head = new_node
        else:
            temp = head
            while temp.next is not None:
                temp = temp.next
            temp.next = new_node
    return head

def traverse_linked_list(head):
    temp = head
    while temp is not None:
        print(temp.data, end=" ")
        temp = temp.next
    print()

def delete_every_nth_node(head, n):
    # https://www.geeksforgeeks.org/dsa/remove-every-k-th-node-linked-list/

    if head is None:
        return None
    if n == 1:
        return head.next
    temp = head
    prev = None

    # Move n-1 steps ahead
    for i in range(n - 1):
        if temp is None:
            break
        prev = temp
        temp = temp.next
    
    # If n is greater than the length of the linked list
    if temp is None:
        return head

    # Delete the nth node
    if prev is None:
        head = temp.next
    else:
        prev.next = temp.next

    # store the next node
    nextNode = temp.next

    # free the memory of the nth node
    temp = None

    # recursively delete the next nth node
    if prev is None:
        return delete_every_nth_node(nextNode, n)    
    prev.next = delete_every_nth_node(nextNode, n)
    return head

if __name__ == "__main__":
    arr = [10, 20, 30, 40, 50]
    print("Creating the linked list:")
    head = create_linked_list(arr)
    print("Traversing the linked list:")
    traverse_linked_list(head)
    print("Deleting every 2nd node:")
    head = delete_every_nth_node(head, 2)
    traverse_linked_list(head)