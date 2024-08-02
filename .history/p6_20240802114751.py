import math



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