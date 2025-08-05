# silent-beam
`mss` and `flask` modules needs to be installed as a global package or `pyinstaller` can not find those.
```python
#Run client
cd client
python client_main.py 192.168.1.1
```
```python
#Compile client
cd client
pyinstaller --hidden-import=mss --onefile --noconsole client_main.py
```
```python
#Compile server
cd host
pyinstaller --hidden-import=flask --onefile --noconsole server.py
```