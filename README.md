# Azubiheft Web API Wrapper


This library provides a Python wrapper for the azubiheft.com web API. With this library, developers can easily manage their Ausbildung (training) reports through a script, allowing for enhanced automation and better control over their Ausbildung documentation.

> **Note**: This repository is a fork of [joshmuente/azubiheft-api](https://github.com/joshmuente/azubiheft-api). Credits to the original author.

## 📖 About Azubiheft

Azubiheft brings a streamlined online approach to training documentation. Designed for businesses, instructors, and apprentices, it offers an effortless way to manage every training entry online. With Azubiheft, you're always one step ahead with all your training data right at your fingertips.

## 🛠 Installation

```bash
pip install azubiheftApi
```

## 🔍 Usage

Here's a quick guide on how to use the `azubiheftApi`:

```python
from azubiheftApi import azubiheftApi
from datetime import datetime

azubiheft = azubiheftApi.Session()
azubiheft.login("yourUserName", "yourPassword")

# Check login status
print(azubiheft.isLoggedIn())

# Get available subjects
subjects = azubiheft.getSubjects()
print(subjects)

# Fetch a report by date
report = azubiheft.getReport(datetime(2023, 10, 19))
print(report)

# Get a week's report ID
week_id = azubiheft.getReportWeekId(datetime.now())
print(week_id)

# Write a new report entry
azubiheft.writeReport(datetime(2023, 10, 19), "Hello World", "2:00", 1)

# Fetch the report again to see changes
report = azubiheft.getReport(datetime(2023, 10, 19))
print(report)

# Log out from the session
azubiheft.logout()

# Check login status (should be False after logging out)
print(azubiheft.isLoggedIn())
```

## 🌱 Contribution

Feel free to fork, star, or contribute to this repository. For any bugs or feature requests, please open a new issue.

---
