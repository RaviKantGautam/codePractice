import math

def countDigitsWitMath(n):
    '''Count the number of digits in a number using math library'''
    return math.floor(math.log10(n)) + 1

def countDigits(n):
    count = 0
    while n != 0:
        n //= 10
        count += 1
    return count

def reverseNumber(n):
    revNum = 0
    while n != 0:
        revNum = revNum * 10 + n % 10
        n //= 10
    return revNum

def findDivisors(n):
    divisors = []
    for i in range(1, n+1):
        if n % i == 0:
            divisors.append(i)
    return divisors

def findDivisorsOptimized(n):
    divisors = []
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
    return divisors

def checkPrime(n):
    cnt = 0
    for i in range(1, n+1):
        if n % i == 0:
            cnt += 1
    return cnt == 2

def checkPrimeOptimized(n):
    if n == 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            cnt += 1
            if n/i != i:
                cnt += 1
    if cnt == 2:
        return True
    return False

def fibonacci(n):
    a, b = 0, 1
    for i in range(n):
        print(a, end=' ')
        a, b = b, a + b

def fibonacciRec(n, a=0, b=1):
    if n == 0:
        return
    print(a, end=' ')
    fibonacciRec(n-1, b, a+b)


def selectionSort(arr):
    for i in range(len(arr)):
        minIndex = i
        for j in range(i+1, len(arr)):
            if arr[j] < arr[minIndex]:
                minIndex = j
        arr[i], arr[minIndex] = arr[minIndex], arr[i]
    return arr

def bubbleSort(arr):
    low = 0
    high = len(arr) - 1
    while low < high:
        for i in range(low, high):
            if arr[i] > arr[i+1]:
                arr[i], arr[i+1] = arr[i+1], arr[i]
        high -= 1
        for i in range(high, low, -1):
            if arr[i] < arr[i-1]:
                arr[i], arr[i-1] = arr[i-1], arr[i]
        low += 1
    return arr

def insertionSort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr


def merge

def main():
    print(insertionSort([-2, 45, 0, 11, -9,88,-97,-202,747]))

if __name__ == "__main__":
    main()