a="abbccdde"
output = "ab2c2d2e"
count = 1
temp = ''

for i in range(1, len(a)):
    if a[i-1] == a[i]:
        count += 1
    if count == 1:
        temp += a[i]
    else:
        temp += a[i]+str(count)
        count == 1
temp+=a[-1]+str(count)

print(temp)