a="abbccdde"
output = "ab2c2d2e"
n = len(a)
count = 1
temp = ''

for i in range(1, n):
    if a[i-1] == a[i]:
        count += 1
    else:
        if count == 1:
            temp += a[i-1]
        else:
            temp += a[i-1]+str(count)
            count = 1
if a[n-1] == a[n]:
    count += 1
    temp
else:
    temp += a[n]
print(temp)