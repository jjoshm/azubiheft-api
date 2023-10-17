# azubiheft-api

Api for azubiheft.de

## install with pip

```
pip install azubiheftApi
```

## usage example code

```python
from azubiheftApi import azubiheftApi
from datetime import datetime

azubiheft = azubiheftApi.Session()

azubiheft.login("yourUserName", "yourPassword")

# Check login status
print(azubiheft.isLoggedIn())

# Testen Sie die getSubjects-Funktion
subjects = azubiheft.getSubjects()
print(subjects)

# Testen Sie die getReport-Funktion
report = azubiheft.getReport(datetime(2023, 10, 19))
print(report)

# Testen Sie die getReportWeekId-Funktion
week_id = azubiheft.getReportWeekId(datetime.now())
print(week_id)

# Use the new writeReport method
azubiheft.writeReport(datetime(2023, 10, 19), "Hello World", "2:00", 1)

# Get a report
report = azubiheft.getReport(datetime(2023, 10, 19))
print(report)

# Testen Sie die logout-Funktion
azubiheft.logout()
# Sollte False zurückgeben, wenn Sie erfolgreich ausgeloggt sind
print(azubiheft.isLoggedIn())
```
