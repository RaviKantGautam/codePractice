def linearSearch(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

def binarySearch(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def binarySearchRecursive(arr, target, left, right):
    if left > right:
        return -1
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binarySearchRecursive(arr, target, mid + 1, right)
    else:
        return binarySearchRecursive(arr, target, left, mid - 1)
    return -1

def jumpSearch(arr, target):
    n = len(arr)
    step = int(n**0.5)
    prev = 0
    while arr[min(step, n)-1] < target:
        prev = step
        step += int(n**0.5)
        if prev >= n:
            return -1
    while arr[prev] < target:
        prev += 1
        if prev == min(step, n):
            return -1
    if arr[prev] == target:
        return prev
    return -1

def interpolationSearch(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) * (target - arr[left]) // (arr[right] - arr[left])
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

def ternarySearch(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid1 = left + (right - left) // 3
        mid2 = right - (right - left) // 3
        if arr[mid1] == target:
            return mid1
        elif arr[mid2] == target:
            return mid2
        elif arr[mid1] < target:
            left = mid1 + 1
        elif arr[mid2] > target:
            right = mid2 - 1
        else:
            left = mid1 + 1
            right = mid2 - 1
    return -1
arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
target = 7
print(linearSearch(arr, target))
print(binarySearch(arr, target))
print(binarySearchRecursive(arr, target, 0, len(arr) - 1))
print(jumpSearch(arr, target))
print(interpolationSearch(arr, target))
print(ternarySearch(arr, target))