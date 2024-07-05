import os
import shutil

# Source directory (replace with the actual path)
source_dir = r'A:\Github repos\Answer\AIProbe\Result\FourRooms\11'

# Destination directory (replace with the desired new location)
new_location = 'A:\Github repos\Answer\AIProbe\Result\FourRooms\SS'

# Create the destination directory if it doesn't exist
os.makedirs(new_location, exist_ok=True)

# Iterate through each environment folder in the source directory
for root, dirs, files in os.walk(source_dir):
    for file in files:
        if file == 'screenshot.png':
            env_folder = os.path.basename(root)
            src_file = os.path.join(root, file)
            dst_file = os.path.join(new_location, f'{env_folder}_screenshot.png')
            shutil.copy(src_file, dst_file)
            print(f'Copied {src_file} to {dst_file}')
