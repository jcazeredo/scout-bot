from abc import ABC, abstractmethod
import requests
from typing import Dict, Any
from .utils import log
import time

class BaseScout(ABC):
    def __init__(self):
        self.session = requests.Session()
        self.setup()

    def setup(self):
        """Initialize scout with configuration"""
        pass

    @abstractmethod
    def perform_search(self) -> Dict[str, Any]:
        """Perform the actual search operation"""
        pass

    @abstractmethod
    def parse_results(self, content: Any) -> Dict[str, Any]:
        """Parse the search results"""
        pass

    def notify(self, message: str):
        """Default notification method (can be overridden)"""
        log(f"Notification: {message}")

    def run(self, max_attempts: int = 5, short_wait: int = 60, long_wait: int = 3600):
        """
        Main execution loop
        Args:
            max_attempts: Maximum attempts per run
            short_wait: Seconds between attempts
            long_wait: Seconds between runs when successful
        """
        run_number = self.load_run_number()

        while True:
            run_number += 1
            self.save_run_number(run_number)

            start_message = f"🚀 Starting run #{run_number}"

            log(start_message)
            self.notify(start_message)

            attempt = 0
            results = None

            while attempt < max_attempts and not results:
                attempt += 1
                try:
                    search_results = self.perform_search()
                    parsed = self.parse_results(search_results)
                    if parsed.get("success", False):
                        results = parsed
                        break
                except Exception as e:
                    error_msg = f"[Attempt #{attempt}] Error during search: {e}"
                    log(error_msg)
                    self.notify(f"⚠️ Error during search (attempt #{attempt}):\n`{e}`")

                self.sleep(short_wait)

            if results:
                self.handle_success(run_number, results)
                self.sleep(long_wait)
            else:
                self.handle_failure(run_number, max_attempts)
                self.sleep(long_wait)

    def sleep(self, seconds: float):
        """Sleep with random jitter"""
        from .utils import random_delay
        delay = random_delay(seconds)
        log(f"Waiting {delay:.1f} seconds...")
        time.sleep(delay)

    def load_run_number(self) -> int:
        """Load the current run number"""
        from .utils import load_run_number
        return load_run_number()

    def save_run_number(self, run_num: int):
        """Save the current run number"""
        from .utils import save_run_number
        save_run_number(run_num)

    def handle_success(self, run_number: int, results: Dict[str, Any]):
        """Handle successful search"""
        message = f"🎉 Success on run #{run_number}!\nResults: {results}"
        self.notify(message)
        log(f"Success on run #{run_number}, results: {results}")

    def handle_failure(self, run_number: int, max_attempts: int):
        """Handle failed search after all attempts"""
        msg = f"❗️ Max attempts ({max_attempts}) reached on run #{run_number}"
        self.notify(msg)
        log(msg)