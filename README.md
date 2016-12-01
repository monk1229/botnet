# Botnet Client Server

## PreRequisites
 - python 3.5 or higher

 Python Libraries installed via pip or otherwise
 - requests
 - psutil

 For building the binaries, `PyInstaller`.

## Running
For this POC you must have the server running in localhost. To change this
modify the `CC_BASE_PATH` variable in `server.py` and `client.py` to
point to the correct location. 

### Server
You have to cd into the server directory and run `python3 server.py`.

### Client
Simply run `python3 client.py` or an already built binary.

## Creating a runnable binary
See the `PyInstaller` docs for more info, but it's as
simple as `PyInstaller client.py -F --hidden-imports queue`. This
will create a single binary under the `dist/` folder. This will
work for the platform currently running. To create binaries for
other platforms, run the same command in a machine running that OS.

If you'd like to encrypt the binary for further obfuscation, you can use
the `PyInstaller` option `--key`. This requires the `PyCrypto` library
installed.

## Future Improvements
A move robust and advanced command mechanism could be developed. This
could help improve making more complex operations by chaining different
commands.

The server and client can be upgraded and improved independent of each
other.
