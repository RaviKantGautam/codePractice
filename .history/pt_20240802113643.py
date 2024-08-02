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




