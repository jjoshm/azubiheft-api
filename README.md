# azubiheft-api
Custom Api for azubiheft.de

## install with pip
<code>pip install git+https://github.com/joshmuente/azubiheft-api</code>

## usage
simply import the module and create a new Session:<br>
```python
from azubiheftApi import azubiheftApi

azubiheft = azubiheftApi.Session()
azubiheft.login("my@email.com", "mypassword")
```
