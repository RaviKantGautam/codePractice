# a="abbbccddc"
# output = "ab2c2d2e"
# n = len(a)
# count = 1
# temp = ''

# for i in range(1, n):
#     if a[i-1] == a[i]:
#         count += 1
#     else:
#         if count == 1:
#             temp += a[i-1]
#         else:
#             temp += a[i-1]+str(count)
#             count = 1
# if count > 1:
#     temp += a[-1]+str(count)
# else:
#     temp += a[-1]
# print(temp)

# frd = open('test.zip', 'rb')
# fwd = open('new.zip', 'wb')
# fwd.write(frd.read())
# fwd.close()
# frd.close()


# a='[{(}]'
# sampler = {')': '(', '}': '{',']':'['}
# stack = []

# def checkpattern(a):
#     for char in a:
#         if char in sampler.values():
#             stack.append(char)
#         else:
#             if char in sampler.keys():
#                 if not stack or sampler[char] != stack.pop():
#                     return False
    
#     return stack == []
    
# print(checkpattern(a))


a='asdfhjkl'
a=list(a)
a=a.sor
    

