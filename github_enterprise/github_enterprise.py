# github_enterprise.py
#
# Copyright 2017 PEAK6 Investments, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class GithubEnterprise(object):
    """Provides a programmatic API over the Site Admin tools for Github Enterprise.

    Requires a Site Admin username and password to login to the UI via Selenium.

    We chose this design as there's no official API for retrieving the list of dormant
    users, paging through the audit log, or to force resync an LDAP user. But it's
    available in the UI so... /shrug
    """

    # Default to ignoring system actions like LDAP sync/suspend/unsuspend for more meaningful events
    AUDIT_FILTER = "-action:user.ldap_sync -action:user.suspend -action:user.unsuspend"

    def __init__(self, username, password, base_url):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")

    def get_dormant_users(self):
        """Returns the list of Dormant Users.

        GHE Site Admin defines Dormant User as:
            Users are considered dormant if they've existed for longer than a month, haven't
            generated any activity within the last month and are not Site Admins. Activity is
            defined as commenting on issues or pull requests, creating issues / pull requests /
            repositories, making any commits on any repositories, or owning any repositories that
            have been pushed to recently.

        :return: list
        """
        self.driver.find_element_by_css_selector("svg.octicon.octicon-rocket").click()
        self.driver.find_element_by_link_text("Dormant users").click()
        users = self.driver.find_elements_by_css_selector(".boxed-group-list.standalone a")
        return [user.text for user in users]

    def resync_user_ldap(self, username):
        """Queues an immediate LDAP resync for a user.

        This is useful if you don't want to wait for the next full resync of all users.
        (Timing controlled by "Synchronize all users" in the GitHub Enterprise Management Console)

        :param username: str
        """
        self.driver.get(self.base_url + "/stafftools/users/%s/admin" % username)
        self.driver.find_element_by_xpath("//button[contains(.,'Sync now')]").click()

    def get_latest_audit_log(self, username, query=AUDIT_FILTER):
        """Returns the latest audit log entry for a user.

        :param username: str the user to audit
        :param query: str or None to filter system actions like LDAP sync, suspend, and unsuspend
        :return: a tuple of datetime and audit event title or (None, None)
        """
        audit_page = self._get_audit_log_page(username, page=1, query=query)
        entries = self._parse_audit_log_entries(audit_page)
        return entries[0] if len(entries) > 0 else (None, None)

    def get_audit_log(self, username, from_date, to_date=None, query=AUDIT_FILTER):
        """
        Queries the Audit Log for all entries for a user between two dates.

        :param username: str the user to audit
        :param from_date: datetime the start date
        :param to_date: datetime or None for today
        :param query: str or None to filter system actions like LDAP sync, suspend, and unsuspend
        :return: list of (datetime, audit event title) tuples
        """
        page = 1
        earliest_date = datetime.today()
        filtered_entries = []
        while earliest_date >= from_date:
            audit_page = self._get_audit_log_page(username, page=page, query=query)
            entries = self._parse_audit_log_entries(audit_page)
            for dt, title in entries:
                if dt >= from_date and (to_date is None or dt <= to_date):
                    filtered_entries.append((dt, title))
            page += 1
            earliest_date = entries[-1][0]
        return filtered_entries

    def __enter__(self):
        """
        Automatically connect to Github Enterprise
        """
        self.driver = webdriver.Chrome(chrome_options=self.chrome_options)
        self.driver.implicitly_wait(30)
        self._login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Automatically disconnect from Github Enterprise
        """
        self.driver.quit()

    def _login(self):
        self.driver.get(self.base_url + "/login")
        self.driver.find_element_by_id("login_field").clear()
        self.driver.find_element_by_id("login_field").send_keys(self.username)
        self.driver.find_element_by_id("password").clear()
        self.driver.find_element_by_id("password").send_keys(self.password)
        self.driver.find_element_by_name("commit").click()

    def _get_audit_log_page(self, username, page, query=AUDIT_FILTER):
        query = ((query or '') + " user:%s" % username).replace(":", "%3A").replace(" ", "+")
        self.driver.get(self.base_url + "/stafftools/audit_log?page=%s&query=%s" % (page, query))
        return self.driver.find_elements_by_css_selector(".audit-log-entry")

    @staticmethod
    def _parse_audit_log_entries(entries):
        audit_log = []
        for entry in entries:
            title = entry.find_elements_by_css_selector('.audit-log-title')[0].text
            dt = entry.find_element_by_tag_name('relative-time').get_attribute('datetime')
            dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")  # return UTC time (which GHE uses)
            audit_log.append((dt, title))
        return audit_log
