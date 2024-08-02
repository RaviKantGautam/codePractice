import os

source_dir = './s_dir'

for i in os.listdir(source_dir):
    if os.path.isfile(os.path.join(source_dir, i)):
        filename, extension = os.path.splitext(i)
        if extension == '.txt':
            print(i)
            with open(os.path.join(source_dir, i), 'r') as f:
                print(f.read())
            print()