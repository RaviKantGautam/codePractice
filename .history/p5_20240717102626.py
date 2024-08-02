import os
import shutil

source_dir = './s_dir'
dest_dir = './d_dir'

if not os.path.exists(source_dir):
    print("Source directory does not exist")
    exit()

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
else:
    

for i in os.listdir(source_dir):
    if os.path.isfile(os.path.join(source_dir, i)):
        filename, extension = os.path.splitext(i)
        print(len(filename))
        if extension == '.xlsx' and len(filename) == 8:
            print(i)  
            shutil.copy(os.path.join(source_dir, i), dest_dir)
            print("File copied successfully")