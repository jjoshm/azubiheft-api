# Azubiheft Web API Wrapper

[![Downloads](https://static.pepy.tech/badge/azubiheftapi)](https://pepy.tech/project/azubiheftapi)
[![Downloads](https://static.pepy.tech/badge/azubiheftapi/month)](https://pepy.tech/project/azubiheftapi)
[![Downloads](https://static.pepy.tech/badge/azubiheftapi/week)](https://pepy.tech/project/azubiheftapi)

This library provides a Python wrapper for azubiheft.com. With this library, developers can easily manage their Ausbildung (training) reports through a script, allowing for enhanced automation and better control over their Ausbildung documentation.

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

# Initialize session
azubiheft = azubiheftApi.Session()

# Login
azubiheft.login("yourUserName", "yourPassword")

# Check login status
print(azubiheft.isLoggedIn())

# Get available subjects
subjects = azubiheft.getSubjects()
print(subjects)

# Add a new subject
azubiheft.add_subject("New Subject")

# Delete an existing subject by ID
azubiheft.delete_subject("subjectId")

# Fetch a report by date
report = azubiheft.getReport(datetime(2023, 10, 19))
print(report)

# Get a week's report ID
week_id = azubiheft.getReportWeekId(datetime.now())
print(week_id)

# Write a new report entry
azubiheft.writeReport(datetime(2023, 10, 19), "Hello World", "2:00", 1)
# its also possible to format the text using \n or just like this
# """
# Hello World
# This is a new line
# """

# Fetch the report again to see changes
report = azubiheft.getReport(datetime(2023, 10, 19), include_formatting=True)  #  include_formatting=True to include formatting
print(report)


# Log out from the session
azubiheft.logout()

# Check login status (should be False after logging out)
print(azubiheft.isLoggedIn())


```

## 🌱 Contribution

Feel free to fork, star, or contribute to this repository. For any bugs or feature requests, please open a new issue.

---
