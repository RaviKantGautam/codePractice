import os

source_dir = './s_dir'
dest_dir = './d_dir'

if not os.path.exists(source_dir):
    print("Source directory does not exist")
    exit()

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

for i in os.listdir(source_dir):
    if os.path.isfile(os.path.join(source_dir, i)):
        filename, extension = os.path.splitext(i)
        if extension == '.xlsx':
            print(i)   
            os.rename(os.path.join(source_dir, i), os.path.join(dest_dir, i))         