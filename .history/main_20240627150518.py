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


# a='asdfhjkl'
# a=list(a)
# a.sort()
# print("".join(a))
# for i in range(0, len(a)-1, 2):
#     a[i], a[i+1] = a[i+1], a[i]
# print("".join(a))

# s=[27, 3, 8, 5, 1, 31]
# s.sort()
# print(s)
# s = [s[0], s.pop()] + s[1:]
# print(s)

s={1:'one',2:'two',3:'three',4:'four',5:'five',6:'six',7:'seven'}

