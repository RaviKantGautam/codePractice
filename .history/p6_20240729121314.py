import math

def countDigits(n):
    return math.floor(math.log10(n))

def main():
    n = int(input("Enter a number: "))
    print(f"The number of digits in {n} is {countDigits(n)}")

if __name__ == "__main__":
    main()