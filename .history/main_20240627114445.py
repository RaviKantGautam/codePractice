a="abbccddc"
count = 1
temp = ''

for i in range(1, len(a)):
    if a[i-1] == a[i]:
        count += 1
    temp += a[i]+