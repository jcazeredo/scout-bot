import os
import re
from typing import Dict, Any
from bs4 import BeautifulSoup
from core.base_scout import BaseScout
from core.utils import log, load_env_vars, send_telegram_message


class VHSBerlinScout(BaseScout):
    def setup(self):
        """Load VHS Berlin specific configuration"""
        required_vars = [
            "URL",
            "KEYWORD_SELECTION_VALUE",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID"
        ]

        self.config = load_env_vars(required_vars)
        self.config.update({
            "LONG_WAIT": int(os.getenv("LONG_WAIT", "3600")),
            "SHORT_WAIT": int(os.getenv("SHORT_WAIT", "60")),
            "MAX_ATTEMPTS": int(os.getenv("MAX_ATTEMPTS", "500"))
        })

    def notify(self, message: str):
        """Send notification via Telegram"""
        send_telegram_message(self.config['TELEGRAM_BOT_TOKEN'], self.config['TELEGRAM_CHAT_ID'], message)

    def perform_search(self) -> Any:
        """Perform the VHS Berlin course search"""
        # Step 1: Initial GET to get cookies + hidden fields
        r = self.session.get(self.config["URL"])
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        hidden_inputs = self._get_hidden_inputs(soup)

        # Step 2: Prepare payload for POST
        payload = self._build_search_payload(hidden_inputs)

        # Step 3: POST request (form submit)
        post_resp = self.session.post(self.config["URL"], data=payload, allow_redirects=False)
        if post_resp.status_code not in [302, 200]:
            raise Exception(f"Unexpected POST response status: {post_resp.status_code}")

        # Step 4: Follow redirects if needed
        content = self._follow_redirects(post_resp)
        return content

    def _get_hidden_inputs(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract hidden form inputs"""
        inputs = {}
        for name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR", "__LASTFOCUS",
                     "__EVENTTARGET", "__EVENTARGUMENT", "__SCROLLPOSITIONX",
                     "__SCROLLPOSITIONY"]:
            tag = soup.find("input", {"name": name})
            inputs[name] = tag["value"] if tag else ""
        return inputs

    def _build_search_payload(self, hidden_inputs: Dict[str, str]) -> Dict[str, str]:
        """Build the search form payload"""
        return {
            "__LASTFOCUS": hidden_inputs["__LASTFOCUS"],
            "__EVENTTARGET": hidden_inputs["__EVENTTARGET"],
            "__EVENTARGUMENT": hidden_inputs["__EVENTARGUMENT"],
            "__VIEWSTATE": hidden_inputs["__VIEWSTATE"],
            "__VIEWSTATEGENERATOR": hidden_inputs["__VIEWSTATEGENERATOR"],
            "__SCROLLPOSITIONX": hidden_inputs["__SCROLLPOSITIONX"],
            "__SCROLLPOSITIONY": hidden_inputs["__SCROLLPOSITIONY"],
            "ctl00$Content$btnSearch": "Suchen",
            "ctl00$Content$SimpleSearch1$SimpleSearchBox$txtSearchTerm": "",
            "ctl00$Content$KeywordsList1$cmbKeyword": self.config["KEYWORD_SELECTION_VALUE"],
            "ctl00$Content$AreaList1$cmbDistricts": "0",
            "ctl00$Content$AdvancedSearch1$SearchBox1$txtSearchTerm": "",
            "ctl00$Content$KeywordsListAdvanced1$cmbKeyword": "-1",
            "ctl00$Content$AreaListAdvanced1$CheckBoxListDistricts$0": "0",
            "ctl00$Content$LyceumSelection1$cmbLyceum": "0",
            "ctl00$Content$TimeDependingInput1$cmbTimeStructur": "0",
            "ctl00$Content$TimeDependingInput1$txtCourseInstructor": "",
            "ctl00$Content$TimeDependingInput1$txtBeginFrom": "",
            "ctl00$Content$TimeDependingInput1$txtEndTo": "",
            "ctl00$Content$CourseNumber1$searchBoxCourseNr$txtSearchTerm": ""
        }

    def _follow_redirects(self, initial_response) -> Any:
        """Follow redirect chain if needed"""
        # First response handling
        if initial_response.status_code == 200:
            return initial_response.text

        loc = initial_response.headers.get("Location")
        if not loc:
            return initial_response.text

        # First redirect
        r1 = self.session.get(f"https://www.vhsit.berlin.de{loc}", allow_redirects=False)
        if r1.status_code == 200:
            return r1.text

        loc2 = r1.headers.get("Location")
        if not loc2:
            return r1.text

        # Second redirect
        r2 = self.session.get(f"https://www.vhsit.berlin.de{loc2}")
        r2.raise_for_status()
        return r2.text

    def parse_results(self, html_text: str) -> Dict[str, Any]:
        """Parse the HTML results from VHS Berlin"""
        soup = BeautifulSoup(html_text, "html.parser")

        # Check for no courses found
        error_el = soup.select_one("#ctl00_Content_ErrorMessage1_lblError")
        if error_el and "Zu Ihrer Suche wurden keine Kurse gefunden." in error_el.text:
            return {"success": False, "has_courses": False}

        # Check for course list title
        title_el = soup.select_one("#ctl00_Content_lblTitle")
        if not title_el or "Kursliste" not in title_el.text:
            return {"success": False, "has_courses": False}

        # Get course count
        count_el = soup.select_one("#ctl00_Content_lblMessage1All")
        count_text = count_el.text.strip() if count_el else ""
        m = re.search(r"\d+", count_text)
        course_count = int(m.group()) if m else 0

        # Parse course rows
        rows = soup.select("#ctl00_Content_ILDataGrid1 tr.DataGridItem")
        courses = []
        for row in rows:
            def safe_text(sel):
                try:
                    el = row.select_one(sel)
                    return el.text.strip() if el else "N/A"
                except:
                    return "N/A"

            courses.append({
                "district": safe_text("td.DataGridItemDistrict"),
                "course_title": safe_text("td.DataGridItemCourseTitle"),
                "free_places": safe_text("td.DataGridItemPlaces")
            })

        return {
            "success": True,
            "has_courses": True,
            "course_count": course_count,
            "courses": courses
        }

    def handle_success(self, run_number: int, results: Dict[str, Any]):
        """Custom success handler for VHS Berlin"""
        message = (
            f"🎉 *Courses available found on run #{run_number}!*\n"
            f"Total courses: *{results['course_count']}*\n"
            f"Link: {self.config['URL']}\n\n"
        )

        for i, c in enumerate(results["courses"], 1):
            message += (
                f"{i}. District: {c['district']}\n"
                f"   Title: {c['course_title']}\n"
                f"   Free places: {c['free_places']}\n\n"
            )

        self.notify(message)
        log(f"Courses found on run #{run_number}, waiting {self.config['LONG_WAIT'] / 60:.1f} minutes before next run...")

    def handle_failure(self, run_number: int, max_attempts: int):
        """Custom failure handler for VHS Berlin"""
        msg = f"❗️ Max attempts ({max_attempts}) reached on run #{run_number}, waiting {self.config['LONG_WAIT'] / 60:.1f} minutes before next run..."
        log(msg)
        self.notify(msg)

    def run(self):
        """Run with VHS Berlin specific configuration"""
        super().run(
            max_attempts=self.config["MAX_ATTEMPTS"],
            short_wait=self.config["SHORT_WAIT"],
            long_wait=self.config["LONG_WAIT"]
        )