# azubiheft-api
Custom Api for azubiheft.de

## install with pip
<code>pip install git+https://github.com/joshmuente/azubiheft-api</code>

## usage
simply import the module
```python
from azubiheftApi import azubiheftApi
```

create a new session
```python
azubiheft = azubiheftApi.Session()
```

login with your azubiheft account
```python
azubiheft.login("my@email.com", "mypassword")
```

and write a new report
```python
azubiheft.writeReport(datetime.now(), "hello world", timedelta(hours=1, minutes=15))
```
