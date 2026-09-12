class Node:
    def __init__(self, data):
        self.data = data
        self.next = None


def traverse_linked_list(head):
    temp = head
    while temp is not None:
        print(temp.data, end=" ")
        temp = temp.next
    print()

def count_nodes(head):
    temp = head
    count = 0
    while temp is not None:
        count += 1
        temp = temp.next
    return count

def search_node(head, key):
    temp = head
    while temp is not None:
        if temp.data == key:
            return True
        temp = temp.next
    return False

def insert_at_beginning(head, data):
    new_node = Node(data)
    new_node.next = head
    return new_node

def insert_at_end(head, data):
    new_node = Node(data)
    temp = head
    while temp.next is not None:
        temp = temp.next
    temp.next = new_node
    return head

def insert_at_position(head, data, position):
    new_node = Node(data)
    temp = head
    for i in range(position - 1):
        temp = temp.next
    new_node.next = temp.next
    temp.next = new_node
    return head

def delete_at_beginning(head):
    temp = head
    head = head.next
    temp.next = None
    return head

def delete_at_end(head):
    temp = head
    while temp.next.next is not None:
        temp = temp.next
    temp.next = None
    return head

def delete_at_position(head, position):
    temp = head
    for i in range(position - 1):
        temp = temp.next
    temp.next = temp.next.next
    return head

def delete_node(head, key):
    temp = head
    while temp.next is not None:
        if temp.next.data == key:
            temp.next = temp.next.next
            return head
        temp = temp.next
    return head

def reverse_linked_list(head):
    prev = None
    current = head
    while current is not None:
        next = current.next
        current.next = prev
        prev = current
        current = next
    return prev

if __name__ == "__main__":
    head = Node(10)
    head.next = Node(20)
    head.next.next = Node(30)
    head.next.next.next = Node(40)
    print("Traversing the linked list:")
    traverse_linked_list(head)
    print("Counting nodes:")
    print(count_nodes(head))
    print("Searching node: 30")
    print(search_node(head, 30))
    print("Inserting at beginning: 5")
    head = insert_at_beginning(head, 5)
    traverse_linked_list(head)
    print("Inserting at end: 50")
    head = insert_at_end(head, 50)
    traverse_linked_list(head)
    print("Inserting at position: 35 at position 3")
    head = insert_at_position(head, 35, 3)
    traverse_linked_list(head)
    print("Deleting at beginning: 5")
    head = delete_at_beginning(head)
    traverse_linked_list(head)
    print("Deleting at end: 50")
    head = delete_at_end(head)
    traverse_linked_list(head)
    print("Deleting at position: 35 at position 3")
    head = delete_at_position(head, 3)
    traverse_linked_list(head)
    print("Deleting node: 35")
    head = delete_node(head, 35)
    traverse_linked_list(head)
    print("Reversing the linked list:")
    head = reverse_linked_list(head)
    traverse_linked_list(head)