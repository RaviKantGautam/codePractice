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
    

def main():
    n = int(input("Enter a number: "))
    print(f"The number of digits in {n} is {reverseNumber(n)}")

if __name__ == "__main__":
    main()