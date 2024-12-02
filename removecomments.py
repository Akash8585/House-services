import os
import re

def remove_comments_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()

    # Remove comments based on file type
    if file_path.endswith('.html'):
        # Remove HTML comments
        code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
        # Remove JavaScript comments within <script> tags
        code = re.sub(r'<script.*?>.*?</script>', lambda m: re.sub(r'//.*|/\*.*?\*/', '', m.group(0), flags=re.DOTALL), code, flags=re.DOTALL)
    elif file_path.endswith('.js'):
        # Remove single-line comments
        code = re.sub(r'//.*', '', code)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)

    # Write the cleaned code back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(code)

def remove_comments_from_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(('.html', '.js')):
                file_path = os.path.join(root, file)
                remove_comments_from_file(file_path)
                print(f"Processed {file_path}")

# Specify the directory containing your codebase
codebase_directory = 'D:/MAD1 project/code'
remove_comments_from_directory(codebase_directory)