#!/usr/bin/python3
# azubiheft.com web-api

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .errors import AuthError, ValueTooLargeError, NotLoggedInError
import time
import re
from typing import List

class Entry:
    def __init__(self, date: datetime, message: str, time_spent: str, entry_type: int):
        self.date = date
        self.message = message
        self.time_spent = time_spent
        self.type = entry_type


class Session():
    def __init__(self):
        self.session: requests.sessions.Session = None

    def login(self, username: str, password: str) -> None:
        if(self.isLoggedIn()):
            raise AuthError("already logged in. Logout first")

        self.session = requests.session()

        loginPageHtml = self.session.get(
            'https://www.azubiheft.de/Login.aspx')

        soup = BeautifulSoup(loginPageHtml.text, 'html.parser')

        """ needed for the login request """
        viewstate = soup.find(id="__VIEWSTATE")['value']
        viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")['value']
        eventvalidation = soup.find(id="__EVENTVALIDATION")['value']

        headers = {
            'content-type': 'application/x-www-form-urlencoded'
        }
        formData = {'__VIEWSTATE': viewstate,
                    '__VIEWSTATEGENERATOR': viewstategenerator,
                    '__EVENTVALIDATION': eventvalidation,
                    'ctl00$ContentPlaceHolder1$txt_Benutzername': username,
                    'ctl00$ContentPlaceHolder1$txt_Passwort': password,
                    'ctl00$ContentPlaceHolder1$chk_Persistent': 'on',
                    'ctl00$ContentPlaceHolder1$cmd_Login': 'Anmelden',
                    'ctl00$ContentPlaceHolder1$HiddenField_isMobile': 'false'
                    }

        self.session.post('https://www.azubiheft.de/Login.aspx',
                          headers=headers, data=formData)
        if(not self.isLoggedIn()):
            raise AuthError("login failed")

    def logout(self) -> None:
        if (not self.session):
            raise NotLoggedInError("not logged in. Login first")
        self.session.get('https://www.azubiheft.de/Azubi/Abmelden.aspx')
        if (not self.isLoggedIn()):
            self.session = None

    def isLoggedIn(self) -> bool:
        if (not self.session):
            return False

        indexHtml = self.session.get(
            'https://www.azubiheft.de/Azubi/Default.aspx').text
        soup = BeautifulSoup(indexHtml, 'html.parser')
        viewstate = soup.find(id="Abmelden")
        if(viewstate):
            return True

        return False

    def getReportWeekId(self, date: datetime) -> str:
        if(self.isLoggedIn()):
            print("Debug: Inside getReportWeekId")
            url = "https://www.azubiheft.de/Azubi/Ausbildungsnachweise.aspx"
            print("Debug: URL:", url)
            overviewHtml = self.session.get(url).text
            soup = BeautifulSoup(overviewHtml, 'html.parser')
            weekDivs = soup.find_all("div", class_="mo NBox")

            # Calculate the calendar week number
            calendar_week = date.isocalendar()[1]
            year = date.isocalendar()[0]

            for div in weekDivs:
                kwDiv = div.find("div", class_="sKW")
                yearDiv = div.find("div", class_="KW").find_all("div")[2]

                if kwDiv and yearDiv:
                    kw = int(kwDiv.get_text(strip=True))
                    kwYear = int(yearDiv.get_text(strip=True))

                    if kw == calendar_week and kwYear == year:
                        weekId = div['onclick'].split("'")[1].split('=')[1]
                        print("Debug: Report ID:", weekId)
                        return weekId

            raise ValueError("No report found for the specified week")
        else:
            raise NotLoggedInError("not logged in. Login first")

    def getSubjects(self) -> list:
        if(self.isLoggedIn()):
            staticSubjects = [
                {'id': 1, 'name': 'Betrieb'},
                {'id': 2, 'name': 'Schule'},
                {'id': 3, 'name': 'ÜBA'},
                {'id': 4, 'name': 'Urlaub'},
                {'id': 5, 'name': 'Feiertag'},
                {'id': 6, 'name': 'Arbeitsunfähig'},
                {'id': 7, 'name': 'Frei'}
            ]
            subjectSetupHtml = self.session.get(
                'https://www.azubiheft.de/Azubi/SetupSchulfach.aspx'
            ).text
            soup = BeautifulSoup(subjectSetupHtml, 'html.parser')
            subjectElements = soup.find(id='divSchulfach').find_all('input')

            subjects = []
            for subjectElement in subjectElements:
                subject = {
                    "id": subjectElement["data-default"], "name": subjectElement["value"]}
                subjects.append(subject)

            return staticSubjects + subjects

        else:
            raise NotLoggedInError("not logged in. Login first")

    def writeReports(self, entries: List[Entry]) -> None:
        if not self.isLoggedIn():
            raise NotLoggedInError("not logged in. Login first")

        headers = {
            'x-my-ajax-request': 'ajax',
            'Origin': 'https://www.azubiheft.de',
            'Referer': 'https://www.azubiheft.de/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
        }

        for entry in entries:
            date_str = TimeHelper.dateTimeToString(entry.date)
            week_number = self.getReportWeekId(entry.date)
            url = f"https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum={date_str}&BrNr={week_number}&BrSt=1&BrVorh=Yes&T={TimeHelper.getActualTimestamp()}"

            formData = {
                'disablePaste': '0',
                'Seq': '0',
                'Art_ID': str(entry.type),
                'Abt_ID': '0',
                'Dauer': entry.time_spent,
                'Inhalt': entry.message,
                'jsVer': '12'
            }

            response = self.session.post(url, headers=headers, data=formData)
            if response.status_code != 200:
                print(f"Failed to add entry for date {date_str}. Response code: {response.status_code}")
                
    def writeReport(self, date: datetime, message: str, time_spent: str, entry_type: int) -> None:
        entry = Entry(date, message, time_spent, entry_type)
        self.writeReports([entry])

    def getReport(self, date: datetime):
        if(self.isLoggedIn()):
            url = "https://www.azubiheft.de/Azubi/Tagesbericht.aspx?Datum=" + \
                TimeHelper.dateTimeToString(date)
            reportHtml = self.session.get(url).text
            soup = BeautifulSoup(reportHtml, 'html.parser')

            tabel = soup.find("table", class_='myTable')
            type = tabel.find_all('div', class_='row1')
            post = tabel.find_all('div', class_='row7')
            dur = tabel.find_all('div', class_='row2')

            reports = []

            for i in range(len(type)):
                typeText = type[i].get_text()
                postText = post[i].get_text()
                durText = dur[i].get_text()

                if durText != "00:00":
                    reports.append({
                        "type": typeText,
                        "post": postText,
                        "dur": durText
                    })

            if len(reports) == 0:
                print("No Reports")
            else:
                return reports
        else:
            raise NotLoggedInError("not logged in. Login first")

class TimeHelper():
    @staticmethod
    def dateTimeToString(date: datetime) -> str:
        return date.strftime("%Y%m%d")

    @staticmethod
    def getActualTimestamp() -> str:
        return str(int(time.time()))

    @staticmethod
    def timeDeltaToString(time: timedelta) -> str:
        maxTime = timedelta(hours=19, minutes=59)
        if(time < maxTime):
            formatted = ':'.join(str(time).split(':')[:2])
            return formatted
        else:
            raise ValueTooLargeError('Max time is ' + str(maxTime))
