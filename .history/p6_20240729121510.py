import math

def countDigitsWitMath(n):
    ''''''
    return math.floor(math.log10(n)) + 1

def countDigits(n):
    count = 0
    while n != 0:
        n //= 10
        count += 1
    return count

def main():
    n = int(input("Enter a number: "))
    print(f"The number of digits in {n} is {countDigits(n)}")

if __name__ == "__main__":
    main()