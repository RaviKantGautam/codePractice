import math

def merge(arr, low, mid, high):
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


def mergeSort(arr, low, high):
    if low < high:
        mid = (low + high) // 2
        mergeSort(arr, low, mid)
        mergeSort(arr, mid+1, high)
        merge(arr, low, mid, high)
    return arr


def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] < pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i+1], arr[high] = arr[high], arr[i+1]
    return i+1


def quickSort(arr, low, high):
    if low < high:
        pivot = partition(arr, low, high)
        quickSort(arr, low, pivot-1)
        quickSort(arr, pivot+1, high)
    return arr


def main():
    # print(insertionSort([-2, 45, 0, 11, -9,88,-97,-202,747]))
    print(mergeSort([-2, 45, 0, 11, -9,88,-97,-202,747], 0, 8))

if __name__ == "__main__":
    main()