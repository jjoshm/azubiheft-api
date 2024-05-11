#!/usr/bin/python3
# azubiheft.com web-api

import requests
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import urllib.parse
import re
import logging
import time

from .errors import AuthError, ValueTooLargeError, NotLoggedInError

# Configure the logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Entry:
    def __init__(self, date: datetime, message: str, time_spent: str, entry_type: int):
        self.date = date
        self.message = message
        self.time_spent = time_spent
        self.type = entry_type

class Session:
    BASE_URL = "https://www.azubiheft.de"

    def __init__(self):
        """Initializes the Azubiheft session."""
        self.session: Optional[requests.sessions.Session] = None

    def login(self, username: str, password: str) -> None:
        """Log in the user with the provided username and password."""
        if self.isLoggedIn():
            raise AuthError("Already logged in. Logout first.")

        self.session = requests.session()
        login_page_html = self.session.get(
            urllib.parse.urljoin(self.BASE_URL, "/Login.aspx")
        )
        soup = BeautifulSoup(login_page_html.text, "html.parser")

        tokens = self._extract_form_tokens(soup)

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        formData = {
            "__VIEWSTATE": tokens["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
            "ctl00$ContentPlaceHolder1$txt_Benutzername": username,
            "ctl00$ContentPlaceHolder1$txt_Passwort": password,
            "ctl00$ContentPlaceHolder1$chk_Persistent": "on",
            "ctl00$ContentPlaceHolder1$cmd_Login": "Anmelden",
            "ctl00$ContentPlaceHolder1$HiddenField_isMobile": "false",
        }

        self.session.post(
            urllib.parse.urljoin(self.BASE_URL, "/Login.aspx"),
            headers=headers,
            data=formData,
        )

        if not self.isLoggedIn():
            raise AuthError("Login failed.")

    def logout(self) -> None:
        """Log out the current user."""
        if not self.session:
            raise NotLoggedInError("Not logged in. Login first.")
        self.session.get(urllib.parse.urljoin(self.BASE_URL, "/Azubi/Abmelden.aspx"))
        self.session = None

    def isLoggedIn(self) -> bool:
        """Check if the user is currently logged in."""
        if not self.session:
            return False

        index_html = self.session.get(
            urllib.parse.urljoin(self.BASE_URL, "/Azubi/Default.aspx")
        ).text
        soup = BeautifulSoup(index_html, "html.parser")
        return bool(soup.find(id="Abmelden"))

    def _fetch_setup_page_tokens(self) -> Dict[str, str]:
        """Fetch the setup page and extract necessary tokens."""
        setup_page = self.session.get(
            urllib.parse.urljoin(self.BASE_URL, "/Azubi/SetupSchulfach.aspx")
        )
        soup = BeautifulSoup(setup_page.text, "html.parser")
        return self._extract_form_tokens(soup)

    def _extract_form_tokens(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract __VIEWSTATE, __VIEWSTATEGENERATOR, and __EVENTVALIDATION tokens from BeautifulSoup object."""
        viewstate = soup.find(id="__VIEWSTATE")
        viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")
        eventvalidation = soup.find(id="__EVENTVALIDATION")
        return {
            "__VIEWSTATE": viewstate["value"] if viewstate else "",
            "__VIEWSTATEGENERATOR": (
                viewstategenerator["value"] if viewstategenerator else ""
            ),
            "__EVENTVALIDATION": eventvalidation["value"] if eventvalidation else "",
        }

    def _prepare_subjects_payload(
        self,
        subjects: List[Dict[str, str]],
        new_subject: Optional[str] = None,
        delete_subject_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """Prepare payload for subject manipulation."""
        payload = {}
        for subject in subjects:
            if delete_subject_id and subject["id"] == delete_subject_id:
                continue
            payload[f'ctl00$ContentPlaceHolder1$txt{subject["id"]}'] = subject["name"]

        if new_subject:
            payload["txtNewSubject"] = new_subject

        return payload

    def add_subject(self, subject_name: str) -> None:
        """Adds a new subject to the list of subjects.
        - Parameters:
            subject_name: Name of the new subject.
        """
        tokens = self._fetch_setup_page_tokens()
        current_subjects = self.getSubjects()

        # Generate a unique key for the new subject
        new_subject_key = f"txt{int(time.time())}"

        payload = {
            "__VIEWSTATE": tokens["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
            new_subject_key: subject_name,  # Add the new subject
            **{
                f'ctl00$ContentPlaceHolder1$txt{subj["id"]}': subj["name"]
                for subj in current_subjects
            },
            "ctl00$ContentPlaceHolder1$cmd_Save": "Speichern",  # Include the save command
        }

        response = self.session.post(
            "https://www.azubiheft.de/Azubi/SetupSchulfach.aspx", data=payload
        )

        if response.status_code != 200:
            print("Failed to add subject. Response code:", response.status_code)
        else:
            print("Subject added successfully.")

    def delete_subject(self, subject_id: str) -> None:
        """Delete a subject from the list of subjects."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        tokens = self._fetch_setup_page_tokens()
        current_subjects = self.getSubjects()

        payload = {
            "__VIEWSTATE": tokens["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
            "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
            "ctl00$ContentPlaceHolder1$HiddenLöschIDs": "," + subject_id,
            **{
                f'ctl00$ContentPlaceHolder1$txt{subj["id"]}': subj["name"]
                for subj in current_subjects
                if subj["id"] != subject_id
            },
            "ctl00$ContentPlaceHolder1$cmd_Save": "Speichern",
        }

        response = self.session.post(
            urllib.parse.urljoin(self.BASE_URL, "/Azubi/SetupSchulfach.aspx"),
            data=payload,
        )

        if response.status_code != 200:
            logger.error(
                f"Failed to delete subject. Response code: {response.status_code}"
            )
        else:
            logger.info("Subject deleted successfully.")

    def getReportWeekId(self, date: datetime) -> str:
        """Get the week ID for a given date."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        url = urllib.parse.urljoin(self.BASE_URL, "/Azubi/Ausbildungsnachweise.aspx")
        overview_html = self.session.get(url).text
        soup = BeautifulSoup(overview_html, "html.parser")
        week_divs = soup.find_all("div", class_="mo NBox")

        calendar_week = date.isocalendar()[1]
        year = date.isocalendar()[0]

        for div in week_divs:
            kw_div = None
            year_div = None
            if "onclick" in div.attrs:
                kw_div = div.find("div", class_="sKW")
                year_div_elements = div.find("div", class_="KW").find_all("div")
                if len(year_div_elements) > 2:
                    year_div = year_div_elements[2]

            if kw_div and year_div:
                kw = int(kw_div.get_text(strip=True))
                kw_year = int(year_div.get_text(strip=True))

                if kw == calendar_week and kw_year == year:
                    week_id = div["onclick"].split("'")[1].split("=")[1]
                    return week_id

        raise ValueError("No report found for the specified week.")

    def getSubjects(self) -> List[Dict[str, str]]:
        """Get the complete list of subjects, including both static and user-defined subjects."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        static_subjects = [
            {"id": "1", "name": "Betrieb"},
            {"id": "2", "name": "Schule"},
            {"id": "3", "name": "ÜBA"},
            {"id": "4", "name": "Urlaub"},
            {"id": "5", "name": "Feiertag"},
            {"id": "6", "name": "Arbeitsunfähig"},
            {"id": "7", "name": "Frei"},
        ]

        subject_setup_html = self.session.get(
            urllib.parse.urljoin(self.BASE_URL, "/Azubi/SetupSchulfach.aspx")
        ).text
        soup = BeautifulSoup(subject_setup_html, "html.parser")
        subject_elements = soup.find(id="divSchulfach").find_all("input")

        dynamic_subjects = [
            {
                "id": subject_element.get("data-default"),
                "name": subject_element.get("value"),
            }
            for subject_element in subject_elements
        ]

        return static_subjects + dynamic_subjects

    def get_art_id_from_text(self, subject_name: str) -> Optional[str]:
        """Get the subject ID from its name."""
        subjects = self.getSubjects()
        for subject in subjects:
            if subject_name in subject['name']:
                return subject['id']
        return None

    def writeReports(self, entries: List[Entry]) -> None:
        """Write a list of reports to the Azubiheft."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        headers = {
            "x-my-ajax-request": "ajax",
            "Origin": self.BASE_URL,
            "Referer": self.BASE_URL,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        for entry in entries:
            date_str = TimeHelper.dateTimeToString(entry.date)
            week_number = self.getReportWeekId(entry.date)
            url = f"{self.BASE_URL}/Azubi/XMLHttpRequest.ashx?Datum={date_str}&BrNr={week_number}&BrSt=1&BrVorh=Yes&T={TimeHelper.getActualTimestamp()}"

            formatted_message = (
                "<div>" + "</div><div>".join(entry.message.split("\n")) + "</div>"
            )
            encoded_message = urllib.parse.quote(formatted_message)

            formData = {
                "disablePaste": "0",
                "Seq": "0",
                "Art_ID": str(entry.type),
                "Abt_ID": "0",
                "Dauer": entry.time_spent,
                "Inhalt": encoded_message,
                "jsVer": "12",
            }

            response = self.session.post(url, headers=headers, data=formData)
            if response.status_code != 200:
                logger.error(
                    f"Failed to add entry for date {date_str}. Response code: {response.status_code}"
                )
            else:
                logger.info(f"Entry added successfully for date {date_str}.")

    def writeReport(
        self, date: datetime, message: str, time_spent: str, entry_type: int
    ) -> None:
        """Write a single report to the Azubiheft."""
        if time_spent.strip() != "00:00":
            entry = Entry(date, message, time_spent, entry_type)
            self.writeReports([entry])

    def getReport(
        self, date: datetime, include_formatting: bool = False
    ) -> List[Dict[str, str]]:
        """Retrieve a report for a given date, optionally including HTML formatting."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        url = f"{self.BASE_URL}/Azubi/Tagesbericht.aspx?Datum={TimeHelper.dateTimeToString(date)}"
        report_html = self.session.get(url).text
        soup = BeautifulSoup(report_html, "html.parser")

        reports = []
        entries = soup.find_all("div", class_="d0 mo")

        for entry in entries:
            duration = entry.find("div", class_="row2 d4").get_text(strip=True)
            if duration.strip() == "00:00":
                continue
            activity_type = (
                entry.find("div", class_="row1 d3")
                .get_text(strip=True)
                .replace("Art: ", "")
            )
            seq = entry.get("data-seq")

            report_text_div = entry.find("div", class_="row7 d5")
            if include_formatting:
                report_text = "".join(
                    str(e)
                    for e in report_text_div.contents
                    if isinstance(e, NavigableString) or e.name == "div"
                )
                report_text = re.sub(r"<br\s*/?>", "\n", report_text)
            else:
                report_text = " ".join(report_text_div.stripped_strings)

            reports.append(
                {
                    "seq": seq,
                    "type": activity_type,
                    "duration": duration,
                    "text": report_text,
                }
            )

        if not reports:
            logger.info("No reports found for the given date.")
        return reports

    def deleteReport(self, date: datetime, entry_number: Optional[int] = None) -> None:
        """Delete one or all reports for a given date."""
        if not self.isLoggedIn():
            raise NotLoggedInError("Not logged in. Login first.")

        report_entries = self.getReport(date)
        if not report_entries:
            logger.info("No report entries found for this date.")
            return

        week_number = self.getReportWeekId(date)

        headers = {
            "x-my-ajax-request": "ajax",
            "Origin": self.BASE_URL,
            "Referer": self.BASE_URL,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

        entries_to_delete = (
            report_entries
            if entry_number is None or entry_number == "all"
            else [report_entries[entry_number - 1]]
        )

        for entry in entries_to_delete:
            formData = {
                'disablePaste': '0',
                'Seq': f"-{entry['seq']}",
                'Art_ID': self.get_art_id_from_text(entry['type']),
                'Abt_ID': '0',
                'Dauer': entry['duration'],
                'Inhalt': entry['text'],
                'jsVer': '12'
            }

            url = f"{self.BASE_URL}/Azubi/XMLHttpRequest.ashx?Datum={TimeHelper.dateTimeToString(date)}&BrNr={week_number}&BrSt=1&BrVorh=Yes&T={TimeHelper.getActualTimestamp()}"

            response = self.session.post(url, headers=headers, data=formData)
            if response.status_code != 200:
                logger.error(
                    f"Failed to delete entry: {entry['text']}. Response code: {response.status_code}"
                )
            else:
                logger.info(f"Entry deleted successfully: {entry['text']}")


class TimeHelper:
    @staticmethod
    def dateTimeToString(date: datetime) -> str:
        """Convert a datetime object to a string in the format YYYYMMDD."""
        return date.strftime("%Y%m%d")

    @staticmethod
    def getActualTimestamp() -> str:
        """Get the current time as a string timestamp."""
        return str(int(time.time()))

    @staticmethod
    def timeDeltaToString(time_delta: timedelta) -> str:
        """Convert a timedelta object to a string, ensuring it's less than 19:59."""
        max_time = timedelta(hours=19, minutes=59)
        if time_delta > max_time:
            raise ValueTooLargeError(f"Max time is {max_time}")
        return str(time_delta)[:-3]
