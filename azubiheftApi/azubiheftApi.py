#!/usr/bin/python3
# azubiheft.com web-api

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .errors import AuthError, ValueTooLargeError, NotLoggedInError
import time
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
        if (self.isLoggedIn()):
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
        if (not self.isLoggedIn()):
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
        if (viewstate):
            return True

        return False

    def _fetch_setup_page_tokens(self):
        """
        Fetches the setup page and extracts necessary tokens.
        Returns a dictionary with '__VIEWSTATE', '__VIEWSTATEGENERATOR', and '__EVENTVALIDATION'.
        """
        setup_page = self.session.get(
            'https://www.azubiheft.de/Azubi/SetupSchulfach.aspx')
        soup = BeautifulSoup(setup_page.text, 'html.parser')

        tokens = {
            '__VIEWSTATE': soup.find(id="__VIEWSTATE")['value'],
            '__VIEWSTATEGENERATOR': soup.find(id="__VIEWSTATEGENERATOR")['value'],
            '__EVENTVALIDATION': soup.find(id="__EVENTVALIDATION")['value']
        }
        return tokens

    def _prepare_subjects_payload(self, subjects, new_subject=None, delete_subject_id=None):
        payload = {}
        for subject in subjects:
            if delete_subject_id and subject['id'] == delete_subject_id:
                continue
            payload[f'ctl00$ContentPlaceHolder1$txt{
                subject["id"]}'] = subject['name']

        if new_subject:
            payload['txtNewSubject'] = new_subject

        return payload

    def add_subject(self, subject_name: str) -> None:
        if not self.isLoggedIn():
            raise NotLoggedInError("not logged in. Login first")

        tokens = self._fetch_setup_page_tokens()
        current_subjects = self.getSubjects()

        # Generate a unique key for the new subject
        new_subject_key = f'txt{int(time.time())}'

        payload = {
            '__VIEWSTATE': tokens['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': tokens['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': tokens['__EVENTVALIDATION'],
            new_subject_key: subject_name,  # Add the new subject
            **{f'ctl00$ContentPlaceHolder1$txt{subj["id"]}': subj["name"] for subj in current_subjects},
            'ctl00$ContentPlaceHolder1$cmd_Save': 'Speichern'  # Include the save command
        }

        response = self.session.post(
            'https://www.azubiheft.de/Azubi/SetupSchulfach.aspx', data=payload)

        if response.status_code != 200:
            print("Failed to add subject. Response code:", response.status_code)
        else:
            print("Subject added successfully.")

    def delete_subject(self, subject_id: str) -> None:
        if not self.isLoggedIn():
            raise NotLoggedInError("not logged in. Login first")

        tokens = self._fetch_setup_page_tokens()
        current_subjects = self.getSubjects()

        # Constructing the payload
        payload = {
            '__VIEWSTATE': tokens['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': tokens['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': tokens['__EVENTVALIDATION'],
            'ctl00$ContentPlaceHolder1$HiddenLöschIDs': ',' + subject_id,  # Add leading comma
            **{f'ctl00$ContentPlaceHolder1$txt{subj["id"]}': subj["name"] for subj in current_subjects if subj["id"] != subject_id},
            'ctl00$ContentPlaceHolder1$cmd_Save': 'Speichern'
        }

        # Sending the request
        response = self.session.post(
            'https://www.azubiheft.de/Azubi/SetupSchulfach.aspx', data=payload)

        if response.status_code != 200:
            print("Failed to delete subject. Response code:", response.status_code)
        else:
            print("Subject deleted successfully.")

    def getReportWeekId(self, date: datetime) -> str:
        if (self.isLoggedIn()):
            url = "https://www.azubiheft.de/Azubi/Ausbildungsnachweise.aspx"
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
                        return weekId

            raise ValueError("No report found for the specified week")
        else:
            raise NotLoggedInError("not logged in. Login first")

    def getSubjects(self) -> list:
        if (self.isLoggedIn()):
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

    def get_art_id_from_text(self, subject_name: str) -> str:
        subjects = self.getSubjects()  # Retrieve all subjects
        for subject in subjects:
            if subject_name in subject['name']:
                return subject['id']
        return None  # Return None if no match found

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
            url = f"https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum={date_str}&BrNr={
                week_number}&BrSt=1&BrVorh=Yes&T={TimeHelper.getActualTimestamp()}"

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
                print(f"Failed to add entry for date {
                      date_str}. Response code: {response.status_code}")

    def writeReport(self, date: datetime, message: str, time_spent: str, entry_type: int) -> None:
        entry = Entry(date, message, time_spent, entry_type)
        self.writeReports([entry])

    def getReport(self, date: datetime):
        if not self.isLoggedIn():
            raise NotLoggedInError("not logged in. Login first")

        url = f"https://www.azubiheft.de/Azubi/Tagesbericht.aspx?Datum={
            TimeHelper.dateTimeToString(date)}"
        reportHtml = self.session.get(url).text
        soup = BeautifulSoup(reportHtml, 'html.parser')

        reports = []
        reportDivs = soup.find_all("div", class_="d0 mo")
        for div in reportDivs:
            typeText = div.find('div', class_='row1').get_text()
            postText = div.find('div', class_='row7').get_text()
            durText = div.find('div', class_='row2').get_text()
            seq = div.get('data-seq')

            if durText != '00:00':
                report = {
                    "seq": seq,
                    "type": typeText,
                    "post": postText,
                    "dur": durText
                }
                reports.append(report)

        return reports

    def deleteReport(self, date: datetime, entry_number: int = None) -> None:
        if not self.isLoggedIn():
            raise NotLoggedInError("not logged in. Login first")

        # Retrieve the report for the specified date
        report_entries = self.getReport(date)
        if not report_entries:
            print("No report entries found for this date.")
            return

        if entry_number is None:
            # Display report entries and ask user which to delete
            for i, entry in enumerate(report_entries, 1):
                print(
                    f"{i}. {entry['type']} - {entry['post']} - {entry['dur']}")
            print("all. Delete all entries")
            choice = input(
                "Select the number of the entry to delete (or 'all' to delete everything): ")
        else:
            choice = str(entry_number)

        if choice.isdigit():
            choice = int(choice) - 1
            if choice < 0 or choice >= len(report_entries):
                print("Invalid entry number.")
                return
            entries_to_delete = [report_entries[choice]]
        elif choice == "all":
            entries_to_delete = report_entries
        else:
            print("Invalid choice.")
            return

        # Retrieve the week number for the specified date
        week_number = self.getReportWeekId(date)

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

        # Loop through and delete each selected entry
        for entry in entries_to_delete:
            formData = {
                'disablePaste': '0',
                'Seq': f"-{entry['seq']}",
                'Art_ID': self.get_art_id_from_text(entry['type']),
                'Abt_ID': '0',
                'Dauer': entry['dur'],
                'Inhalt': entry['post'],
                'jsVer': '12'
            }

            url = f"https://www.azubiheft.de/Azubi/XMLHttpRequest.ashx?Datum={TimeHelper.dateTimeToString(
                date)}&BrNr={week_number}&BrSt=1&BrVorh=Yes&T={TimeHelper.getActualTimestamp()}"

            response = self.session.post(url, headers=headers, data=formData)
            if response.status_code != 200:
                print(f"Failed to delete entry: {
                      entry['post']}. Response code: {response.status_code}")
            else:
                print(f"Entry deleted successfully: {entry['post']}")


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
        if (time < maxTime):
            formatted = ':'.join(str(time).split(':')[:2])
            return formatted
        else:
            raise ValueTooLargeError('Max time is ' + str(maxTime))
