#!/usr/bin/python3
# azubiheft.com web-api

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .errors import AuthError, ValueTooLargeError, NotLoggedInError
import time
import re


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
            url = "https://www.azubiheft.de/Azubi/Wochenansicht.aspx?T=" + \
                TimeHelper.dateTimeToString(date)
            reportHtml = self.session.get(url).text
            soup = BeautifulSoup(reportHtml, 'html.parser')
            id = soup.find(id="lblNachweisNr")["data-br-nr"]
            return id
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

    def writeReport(self, date: datetime, message: str, time: timedelta, type: int = 1) -> None:
        if(self.isLoggedIn()):
            url = "https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum=" + TimeHelper.dateTimeToString(
                date) + " &BrNr=" + self.getReportWeekId(date) + "&T=" + TimeHelper.getActualTimestamp()
            headers = {
                'content-type': 'application/x-www-form-urlencoded'
            }

            formData = {"Seq": 0, "Art_ID": type, "Abt_ID": 0,
                        "Dauer": TimeHelper.timeDeltaToString(time), "Inhalt": message, "jsVer": 11}
            self.session.post(url, data=formData, headers=headers)
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