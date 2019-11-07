#!/usr/bin/python3
# azubiheft.com web-api
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time


class Session():
    def __init__(self):
        self.session: requests.sessions.Session = None

    def login(self, username: str, password: str):
        if(self.isLoggedIn()):
            print("azubiheft: already logged in. Logout first ...")
            return

        print("azubiheft: logging in ...")
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
        if(self.isLoggedIn()):
            print("azubiheft: login successful ...")
        else:
            print("azubiheft: login failed ...")

    def logout(self):
        if (not self.session):
            print("azubiheft: cant't logout because not logged in ...")
            return
        self.session.get('https://www.azubiheft.de/Azubi/Abmelden.aspx')
        if (not self.isLoggedIn()):
            print("azubiheft: logout successful ...")
            self.session = None

    def isLoggedIn(self):
        if (not self.session):
            return False

        indexHtml = self.session.get(
            'https://www.azubiheft.de/Azubi/Default.aspx').text
        soup = BeautifulSoup(indexHtml, 'html.parser')
        viewstate = soup.find(id="Abmelden")
        if(viewstate):
            return True

        return False

    def getReportWeekId(self, date: datetime):
        if(self.isLoggedIn()):
            url = "https://www.azubiheft.de/Azubi/Wochenansicht.aspx?T=" + \
                TimeHelper.dateTimeToString(date)
            reportHtml = self.session.get(url).text
            soup = BeautifulSoup(reportHtml, 'html.parser')
            id = soup.find(id="lblNachweisNr")["data-br-nr"]
            return id
        else:
            print("azubiheft: can't get id because not loggen in ...")

    def writeReport(self, date: datetime, message: str, time: timedelta):
        if(self.isLoggedIn()):
            url = "https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum=" + TimeHelper.dateTimeToString(
                date) + " &BrNr=" + self.getReportWeekId(date) + "&T=" + TimeHelper.getActualTimestamp()
            headers = {
                'content-type': 'application/x-www-form-urlencoded'
            }

            formData = {"Seq": 0, "Art_ID": 1, "Abt_ID": 0,
                        "Dauer": "00:45", "Inhalt": message, "jsVer": 11}
            self.session.post(url, data=formData, headers=headers)
            print("azubiheft: write successful ...")
        else:
            print("azubiheft: can't write because not loggen in ...")


class TimeHelper():
    @classmethod
    def dateTimeToString(cls, date: datetime):
        return date.strftime("%Y%m%d")

    @classmethod
    def getActualTimestamp(cls):
        return str(int(time.time()))

    @classmethod
    def timeDeltaToString(cls, date: datetime):
        pass
