class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None


class BinaryTree:
    def __init__(self, root):
        self.root = root

    def traverse_in_order(self, node):
        if node is not None:
            self.traverse_in_order(node.left)
            print(node.value)
            self.traverse_in_order(node.right)
            return
        
    def traverse_pre_order(self, node):
        if node is not None:
            print(node.value)
            self.traverse_pre_order(node.left)
            self.traverse_pre_order(node.right)
            return

    def traverse_post_order(self, node):
        if node is not None:
            self.traverse_post_order(node.left)
            self.traverse_post_order(node.right)
            print(node.value)
            return

    def traverse_level_order(self):
        if self.root is None:
            return
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            print(node.value)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)

    def height(self, node):
        if node is None:
            return 0
        left_height = self.height(node.left)
        right_height = self.height(node.right)
        return max(left_height, right_height) + 1

    def size(self, node):
        if node is None:
            return 0
        return 1 + self.size(node.left) + self.size(node.right)

    def find_max(self, node):
        if node is None:
            return float('-inf')
        left_max = self.find_max(node.left)
        right_max = self.find_max(node.right)
        return max(node.value, left_max, right_max)

    def find_min(self, node):
        if node is None:
            return float('inf')
        left_min = self.find_min(node.left)
        right_min = self.find_min(node.right)
        return min(node.value, left_min, right_min)

    def find(self, node, value):
        if node is None:
            return False
        if node.value == value:
            return True
        return self.find(node.left, value) or self.find(node.right, value)

    def find_parent(self, node, value):
        if node is None or node.value == value:
            return None
        if (node.left is not None and node.left.value == value) or (node.right is not None and node.right.value == value):
            return node
        left_parent = self.find_parent(node.left, value)
        if left_parent is not None:
            return left_parent
        return self.find_parent(node.right, value)

    def find_leaf_nodes(self, node):
        if node is None:
            return []
        if node.left is None and node.right is None:
            return [node.value]
        return self.find_leaf_nodes(node.left) + self.find_leaf_nodes(node.right)

    def find_non_leaf_nodes(self, node):
        if node is None:
            return []
        if node.left is not None or node.right is not None:
            return [node.value] + self.find_non_leaf_nodes(node.left) + self.find_non_leaf_nodes(node.right)
        return []

    def find_internal_nodes(self, node):
        if node is None:
            return []
        if node.left is not None and node.right is not None:
            return [node.value] + self.find_internal_nodes(node.left) + self.find_internal_nodes(node.right)
        return self.find_internal_nodes(node.left) + self.find_internal_nodes(node.right)

    def find_root(self):
        return self.root

    def find_depth(self, node, value, depth=0):
        if node is None:
            return -1
        if node.value == value:
            return depth
        left_depth = self.find_depth(node.left, value, depth + 1)
        if left_depth != -1:
            return left_depth
        return self.find_depth(node.right, value, depth + 1)

    def create_node(self, value):
        return Node(value)

    def add_node(self, parent, value, is_left=True):
        new_node = self.create_node(value)
        if parent is None:
            if self.root is None:
                self.root = new_node
            return new_node
        if is_left:
            parent.left = new_node
        else:
            parent.right = new_node
        return new_node

    def remove_node(self, parent, value):
        if parent is None:
            if self.root and self.root.value == value:
                self.root = None
            return
        if parent.left and parent.left.value == value:
            parent.left = None
        elif parent.right and parent.right.value == value:
            parent.right = None

        # If the node to be removed is not found among the children of the given parent, recursively search in the subtrees
        if parent.left:
            self.remove_node(parent.left, value)
        if parent.right:
            self.remove_node(parent.right, value)

        return

    