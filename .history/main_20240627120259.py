a="abbccdde"
output = "ab2c2d2e"
count = 1
temp = ''

for i in range(1, len(a)):
    if a[i-1] == a[i]:
        count += 1
    else:
    if count == 1:
        temp += a[i-1]
    else:
        temp += a[i-1]+str(count)
        count = 1
temp+=a[-1]+str(count)

print(temp)