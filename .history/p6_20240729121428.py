import math

def countDigitsWitMath(n):
    return math.floor(math.log10(n)) + 1

def main():
    n = int(input("Enter a number: "))
    print(f"The number of digits in {n} is {countDigits(n)}")

if __name__ == "__main__":
    main()