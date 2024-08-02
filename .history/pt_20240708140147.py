lst = ['lump', 'eat', 'me', 'tea', 'em', 'plum', 'abc']
# The grouped Anagrams : [['lump', 'plum'], ['eat', 'tea'], ['me', 'em'], ['abc']]

output = {}

for i in lst:
    anagram_id = "".join(sorted(i))
    if anagram_id in output:        
        output[anagram_id].append(i)
    else:
        output[anagram_id] = [i]

print(output)
# -------------
data = {"Amit" : "TL",
       "Ravi" : "HR",
       "Reena" : 'PM',
       "Mohan" : "TL",
       "Kapil" : "TL",
       "Rajesh" : "HR",
       "Geeta" : "TL"}

# output = 
# {
# 'TL': ['Amit', 'Mohan', 'Kapil', 'Geeta'],
# 'HR': ['Ravi', 'Rajesh'],
# 'PM': ['Reena']
# }

output = {}
for key,val in data.items():
    if val in output:
        output[val].append(key)
    else:
        output[val] = [key]
print(output)

# ---------
mystr = "aabuuurttppa" 
# output a2bu3rt2p2a

result_lt = []
count = 1

for i in range(1, len(mystr)):
    if mystr[i] == mystr[i-1]:
        count += 1
    else:
        if count == 1:
            result_lt.append(mystr[i-1])
        else:
            result_lt.append(mystr[i-1] + str(count))
        count = 1
result_lt.append(mystr[-1])

print("".join(result_lt))




input_list={
    "set1":['1','67','93','58'],
    "set2":['6','671','83','587'],
    "set3":['-1','6766','873','5845'],
    "set4":['8','6787','8365','58549'],
    "set5":['90','67900','83434','5832'],
    "set6":['45','675656','8312','58312']
}

temp_list = [0,0,0,0]

for key,val in input_list.items():
    index = 0
    for item in val:
        temp_list[index] += int(val[index])
        index +=1
        
print(temp_list)
max_val = max(temp_list)
print("Max Value: ", max_val)
print("index is: ", temp_list.index(max_val))


# ------------

input_dictionary = {"a":{"b":{}},"c":{"d":{}},"e":{"f":{}}} 
output_dictionary={"b":{"a":{}},"d":{"c":{}},"f":{"e":{}}}

temp = {}

for key,value in input_dictionary.items():
    if isinstance(value, dict):
        temp[list(value.keys())[0]] = {key: list(value.values())[0]}

print(temp)




