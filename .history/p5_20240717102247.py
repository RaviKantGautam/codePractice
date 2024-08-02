import os

source_dir = './s_dir'
dest_dir = './d_dir'

if not os.path.exists(source_dir):
    print("")

for i in os.listdir(source_dir):
    if os.path.isfile(os.path.join(source_dir, i)):
        filename, extension = os.path.splitext(i)
        if extension == '.xlsx':
            print(i)            