import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from azubiheftApi.azubiheftApi import Session, Entry, TimeHelper
from azubiheftApi.errors import AuthError, ValueTooLargeError, NotLoggedInError


class TestTimeHelper(unittest.TestCase):
    def test_dateTimeToString(self):
        date = datetime(2024, 5, 10)
        self.assertEqual(TimeHelper.dateTimeToString(date), "20240510")

    def test_getActualTimestamp(self):
        with patch("time.time", return_value=1657890000):
            self.assertEqual(TimeHelper.getActualTimestamp(), "1657890000")

    def test_timeDeltaToString(self):
        time_delta = timedelta(hours=10, minutes=30)
        self.assertEqual(TimeHelper.timeDeltaToString(time_delta), "10:30")

        with self.assertRaises(ValueTooLargeError):
            TimeHelper.timeDeltaToString(timedelta(hours=20))


class TestSession(unittest.TestCase):
    def setUp(self):
        self.session = Session()

    @patch("requests.session")
    def test_login_success(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<input id="__VIEWSTATE" value="state" /><input id="__VIEWSTATEGENERATOR" value="generator" /><input id="__EVENTVALIDATION" value="validation" />'
        mock_session.post.return_value.status_code = 200
        mock_session.get.return_value.text = '<div id="Abmelden"></div>'

        self.session.login("username", "password")
        self.assertTrue(self.session.isLoggedIn())

    @patch("requests.session")
    def test_login_failure(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<input id="__VIEWSTATE" value="state" /><input id="__VIEWSTATEGENERATOR" value="generator" /><input id="__EVENTVALIDATION" value="validation" />'
        mock_session.post.return_value.status_code = 200
        mock_session.get.return_value.text = ""

        with self.assertRaises(AuthError):
            self.session.login("username", "password")

    @patch("requests.session")
    def test_logout(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session

        # Before logout, simulate logged-in state
        mock_session.get.side_effect = [
            MagicMock(text='<div id="Abmelden"></div>'),  # Initial state, logged in
            MagicMock(text=""),  # After logout, not logged in
        ]

        self.session.session = mock_session
        self.session.logout()

        # Check if session is None after logout
        self.assertIsNone(self.session.session)

    @patch("requests.session")
    def test_isLoggedIn(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<div id="Abmelden"></div>'

        self.session.session = mock_session
        self.assertTrue(self.session.isLoggedIn())

        mock_session.get.return_value.text = ""
        self.assertFalse(self.session.isLoggedIn())

    @patch("requests.session")
    def test_add_subject(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<input id="__VIEWSTATE" value="state" /><input id="__VIEWSTATEGENERATOR" value="generator" /><input id="__EVENTVALIDATION" value="validation" />'
        mock_session.post.return_value.status_code = 200

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)
        self.session.getSubjects = MagicMock(return_value=[{"id": "1", "name": "Math"}])

        self.session.add_subject("Physics")
        self.assertTrue(mock_session.post.called)

    @patch("requests.session")
    def test_delete_subject(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<input id="__VIEWSTATE" value="state" /><input id="__VIEWSTATEGENERATOR" value="generator" /><input id="__EVENTVALIDATION" value="validation" />'
        mock_session.post.return_value.status_code = 200

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)
        self.session.getSubjects = MagicMock(return_value=[{"id": "1", "name": "Math"}])

        self.session.delete_subject("1")
        self.assertTrue(mock_session.post.called)

    @patch("requests.session")
    def test_getReportWeekId(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session

        mock_session.get.return_value.text = """
        <div class="mo NBox" onclick="location.href='?week_id=19'">
            <div class="sKW">19</div>
            <div class="KW">
                <div></div>
                <div></div>
                <div>2024</div>
            </div>
        </div>
        """

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)

        # The date here should match the week number and year in the mock data
        week_id = self.session.getReportWeekId(datetime(2024, 5, 10))
        self.assertEqual(week_id, "19")

    @patch("requests.session")
    def test_getSubjects(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = (
            '<div id="divSchulfach"><input data-default="8" value="Extra" /></div>'
        )

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)

        subjects = self.session.getSubjects()
        self.assertIn({"id": "8", "name": "Extra"}, subjects)

    @patch("requests.session")
    def test_writeReports(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.post.return_value.status_code = 200

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)
        self.session.getReportWeekId = MagicMock(return_value="19")

        entry = Entry(datetime(2024, 5, 10), "Did some work", "01:00", 1)
        self.session.writeReports([entry])
        self.assertTrue(mock_session.post.called)

    @patch("requests.session")
    def test_getReport(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session
        mock_session.get.return_value.text = '<div class="d0 mo"><div class="row2 d4">01:00</div><div class="row1 d3">Art: Work</div><div class="row7 d5">Did some work</div></div>'

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)

        reports = self.session.getReport(datetime(2024, 5, 10))
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["type"], "Work")

    @patch("requests.session")
    def test_deleteReport(self, mock_requests):
        mock_session = MagicMock()
        mock_requests.return_value = mock_session

        # Mocking .get to return an HTML structure in .text
        mock_session.get.return_value.text = '<html><div id="divSchulfach"><input data-default="1" value="Math" /></div></html>'

        mock_session.post.return_value.status_code = 200

        self.session.session = mock_session
        self.session.isLoggedIn = MagicMock(return_value=True)
        self.session.getReport = MagicMock(
            return_value=[
                {
                    "seq": "1",
                    "type": "Work",
                    "duration": "01:00",
                    "text": "Did some work",
                }
            ]
        )
        self.session.getReportWeekId = MagicMock(return_value="19")

        self.session.deleteReport(datetime(2024, 5, 10), 1)
        self.assertTrue(mock_session.post.called)


if __name__ == "__main__":
    unittest.main()
