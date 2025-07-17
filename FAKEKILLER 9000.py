import json
import time
import random
import sys
import os
import platform
import shutil
import zipfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import urllib.request
from colorama import init, Fore, Back, Style
from tqdm import tqdm

init(autoreset=True, convert=True)

def setup_terminal():
    os.system('clear' if os.name == 'posix' else 'cls')
    if os.name == 'posix':
        os.system('printf "\033[8;30;120t"')

def print_option(number, text, description=""):
    print(f"{Fore.GREEN}[{number}] {Fore.WHITE}{text}")
    if description:
        print(f"{Fore.LIGHTBLACK_EX}    {description}")

def quick_success(message):
    print(f"{Fore.GREEN}✅ {message}")
    time.sleep(0.1)

def quick_error(message):
    print(f"{Fore.RED}❌ {message}")
    time.sleep(0.1)

def quick_warning(message):
    print(f"{Fore.YELLOW}⚠️  {message}")
    time.sleep(0.1)

def quick_info(message):
    print(f"{Fore.BLUE}ℹ️  {message}")
    time.sleep(0.1)

def quick_loading(message="Loading"):
    print(f"{Fore.CYAN}⏳ {message}...", end='', flush=True)
    time.sleep(0.2)
    print()

def fast_typewriter(text, color=Fore.WHITE):
    for char in text:
        print(f"{color}{char}", end='', flush=True)
        time.sleep(0.002)
    print()

def quick_header(title):
    print(f"\n{Fore.YELLOW}{'='*60}")
    fast_typewriter(f"📋 {title}", Fore.YELLOW)
    print(f"{Fore.YELLOW}{'='*60}")

def quick_clear():
    os.system('clear' if os.name == 'posix' else 'cls')
    show_banner()

TARGETS_FILE = "targets.txt"
MY_PROFILE_FILE = "my_friend_account.txt"
COOKIES_FILE = "cookies.json"
LOG_FILE = "report_log.txt"

MAX_REPORTS_PER_TARGET = 30
SAFE_REPORT_LIMIT = 8
CHROMEDRIVER_BIN = "./chromedriver"

def log_result(profile_url, status, stage=None, error=None, suggestion=None):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if status == 'success':
        icon = '✅'
        label = 'SUCCESS'
        msg = f'{now} | {icon} {label} | {profile_url} | Report sent successfully'
    elif status == 'failed':
        icon = '❌'
        label = 'FAILED'
        msg = f'{now} | {icon} {label} | {profile_url} | Failed at stage: {stage}'
        if error:
            msg += f' | Error: {error}'
        if suggestion:
            msg += f' | Suggestion: {suggestion}'
    elif status == 'warning':
        icon = '⚠️'
        label = 'WARNING'
        msg = f'{now} | {icon} {label} | {profile_url} | {stage or "Warning"}'
        if suggestion:
            msg += f' | Suggestion: {suggestion}'
    else:
        icon = 'ℹ️'
        label = 'INFO'
        msg = f'{now} | {icon} {label} | {profile_url} | {stage or status}'
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def random_delay(a=1.2, b=2.0):
    time.sleep(random.uniform(a, b))

def download_chromedriver():
    print("\U0001F310 Trying to download compatible ChromeDriver...")
    version_url = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
    try:
        with urllib.request.urlopen(version_url) as response:
            data = json.loads(response.read().decode())
            chrome_version = None
            for v, details in data['channels'].items():
                if 'downloads' in details and 'chromedriver' in details['downloads']:
                    for item in details['downloads']['chromedriver']:
                        if 'linux64' in item['platform']:
                            chrome_version = details['version']
                            driver_url = item['url']
                            break
                if chrome_version:
                    break
            if not chrome_version:
                print("❌  Couldn't find compatible version for linux64")
                return False

            print(f"⬇️  Downloading ChromeDriver version {chrome_version}...")

            def download_with_progress(url, filename):
                with urllib.request.urlopen(url) as response:
                    total = int(response.getheader('Content-Length').strip())
                    with open(filename, 'wb') as f, tqdm(
                        total=total, unit='B', unit_scale=True, unit_divisor=1024, desc='Downloading', ncols=70
                    ) as bar:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            bar.update(len(chunk))

            download_with_progress(driver_url, "chromedriver.zip")

            with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
                zip_ref.extractall(".")
            extracted_path = "chromedriver-linux64/chromedriver"
            if os.path.exists(extracted_path):
                shutil.move(extracted_path, CHROMEDRIVER_BIN)
                os.chmod(CHROMEDRIVER_BIN, 0o755)
                shutil.rmtree("chromedriver-linux64")
                os.remove("chromedriver.zip")
                print("✅   ChromeDriver downloaded and ready.")
                return True
            else:
                print("❌  Extracted driver not found")
                return False
    except Exception as e:
        print(f"❌  Failed to download ChromeDriver: {e}")
        return False

def load_cookies(driver, path):
    with open(path, "r") as f:
        cookies = json.load(f)
    driver.get("https://www.facebook.com/")
    for cookie in cookies:
        if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
            cookie['sameSite'] = 'Lax'
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"⚠️  Error adding cookie {cookie.get('name', '')}: {e}")
    driver.refresh()
    random_delay(1, 2)

def check_login(driver):
    driver.get("https://www.facebook.com/")
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'profile.php') or contains(@href, '/me/') or contains(@href, '/home')]"))
        )
        print("✅ Cookies are valid, you are logged in.")
        return True
    except:
        print("❌ Cookies are invalid or expired. Please update your cookies.")
        log_result('N/A', 'failed', 'login', 'Cookies are invalid or expired', 'Update your cookies.json with fresh cookies from your browser.')
        return False

def check_facebook_security(driver):
    try:
        security_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'Security Check') or contains(text(), 'Verify')]")
        if security_elements:
            print("⚠️ Facebook security check detected! Please verify manually.")
            return False
        return True
    except:
        return True

def extract_identifier_from_loaded_page(driver, url):
    driver.get(url)
    random_delay(2, 3)
    clean_url = driver.current_url.split('?')[0]
    print(f"🔗 Loaded clean URL: {clean_url}")
    if "id=" in clean_url:
        return clean_url.split("id=")[-1].split("&")[0]
    else:
        return clean_url.rstrip("/").split("/")[-1]

def retry(func, retries=3, delay=1, *args, **kwargs):
    last_exception = None
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            time.sleep(delay)
    if last_exception is not None:
        raise last_exception
    else:
        raise Exception('Unknown error in retry')

def report_account(driver, profile_url, friend_identifier, report_type="me", fast=False):
    print(f"\n🚨 Reporting profile: {profile_url}")
    if not check_facebook_security(driver):
        print("Stopping due to security check...")
        log_result(profile_url, 'warning', 'Facebook security check detected', None, 'Complete the security check manually, then re-run the script.')
        return

    def do_report():
        driver.get(profile_url)
        random_delay(3, 4) if not fast else random_delay(1.5, 2.5)
        try:
            menu = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Profile settings see more options']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", menu)
            random_delay()
            menu.click()
            random_delay()
            print("✅  Clicked: ⋯ ")
        except Exception as e:
            return 'menu', e
        try:
            report_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Report profile')]"))
            )
            report_btn.click()
            random_delay()
            print("✅  Clicked: Report profile")
        except Exception as e:
            return 'report', e
        try:
            fake_profile = WebDriverWait(driver, 7).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button']//span[contains(text(), 'Fake profile')]"))
            )
            fake_profile.click()
            random_delay()
            print("✅  Clicked: Fake profile")
        except Exception as e:
            return 'fake', e
        if report_type == "friend":
            try:
                friend_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'A friend')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", friend_btn)
                friend_btn.click()
                random_delay()
            except Exception as e:
                return 'friend', e
            try:
                next_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, "//span/span[text()='Next']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                random_delay(0.5, 1)
                try:
                    next_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", next_btn)
                random_delay()
                print("✅  Clicked: Next (after A Friend)")
            except Exception as e:
                return 'next_friend', e
            try:
                search_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='search' and @aria-label='Name']"))
                )
                search_box.clear()
                search_box.send_keys(friend_identifier)
                random_delay(2, 3)
                search_box.send_keys(Keys.ARROW_DOWN)
                time.sleep(1.5)
                search_box.send_keys(Keys.ENTER)
                print("✅  Selected: friend")
                random_delay()
                confirm_friend_btn = WebDriverWait(driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, "//span/span[text()='Next']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", confirm_friend_btn)
                random_delay(0.5, 1)
                try:
                    confirm_friend_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", confirm_friend_btn)
                random_delay()
                print("✅  Clicked: Next")
            except Exception as e:
                return 'select_friend', e
        else:
            try:
                me_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Me' and contains(@class, 'x1lliihq')]"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", me_btn)
                me_btn.click()
                random_delay()
                print("✅  Clicked: Me")
            except Exception as e:
                return 'me', e
        try:
            submit_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//span/span[text()='Submit']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
            submit_btn.click()
            random_delay()
            print("✅  Submitted: successfully")
        except Exception as e:
            return 'submit', e
        try:
            next2_btn = WebDriverWait(driver, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//span/span[text()='Next']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", next2_btn)
            next2_btn.click()
            random_delay()
            print("✅  Clicked: Next")
        except Exception as e:
            return 'next2', e
        try:
            done_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Done']"))
            )
            done_btn.click()
            random_delay(0.5, 1)
            print("✅  Clicked: Done")
        except Exception as e:
            print("⚠️  Couldn't click Done (optional)")
            log_result(profile_url, "info", "Done button not found, but report sent")
            return None, None
    for attempt in range(2):
        result = do_report()
        if result is None:
            return
        stage, error = result
        print(f"🔄 Retrying: Problem occurred at stage {stage}, refreshing and trying again...")
        driver.refresh()
        random_delay(2, 3)
    print(f"❌ Failed at stage {stage} after 2 attempts. Details: {error}")
    suggestion = None
    if stage == 'submit':
        suggestion = 'Facebook layout may have changed. Try updating the script or check manually.'
    elif stage == 'menu' or stage == 'report' or stage == 'fake':
        suggestion = 'Make sure the account is accessible and the page layout is standard.'
    elif stage == 'friend' or stage == 'next_friend' or stage == 'select_friend':
        suggestion = 'Check the friend profile URL and try again.'
    log_result(profile_url, 'failed', stage, error, suggestion)

def show_disclaimer():
    quick_clear()
    quick_header("⚠️  LEGAL DISCLAIMER & USER WARNING")
    print(f"{Fore.RED}{Style.BRIGHT}🔴 CRITICAL WARNINGS:")
    fast_typewriter(f"{Fore.RED}• Using FakeKiller 9000 may result in PERMANENT Facebook account suspension.")
    fast_typewriter(f"{Fore.RED}• Automated reporting violates Facebook Terms of Service.")
    fast_typewriter(f"{Fore.RED}• Repeated misuse may lead to legal consequences depending on your country.")
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️  YOU ARE FULLY RESPONSIBLE FOR YOUR ACTIONS.")
    fast_typewriter(f"{Fore.YELLOW}• FakeKiller 9000 does NOT guarantee any result.")
    fast_typewriter(f"{Fore.YELLOW}• Use ONLY for educational and ethical purposes.")
    print(f"\n{Fore.CYAN}{Style.BRIGHT}📘 EDUCATIONAL DISCLAIMER:")
    fast_typewriter(f"{Fore.WHITE}• FakeKiller 9000 was created for research and automation learning only.")
    fast_typewriter(f"{Fore.WHITE}• The developers of this tool hold NO responsibility for how it is used.")
    print(f"\n{Fore.GREEN}{Style.BRIGHT}💡 SAFETY RECOMMENDATIONS:")
    fast_typewriter(f"{Fore.WHITE}• Do not exceed {SAFE_REPORT_LIMIT} reports per profile.")
    fast_typewriter(f"{Fore.WHITE}• Always use valid cookies.")
    fast_typewriter(f"{Fore.WHITE}• Avoid running from your main personal account.")
    fast_typewriter(f"{Fore.WHITE}• Use VPN or proxy for additional safety.")
    fast_typewriter(f"{Fore.WHITE}• Consider manual reporting before using automation.")
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}🔧 TECHNICAL NOTES:")
    fast_typewriter(f"{Fore.WHITE}• Uses Selenium WebDriver + Headless Chrome.")
    fast_typewriter(f"{Fore.WHITE}• Requires valid 'cookies.json' and 'targets.txt'.")
    fast_typewriter(f"{Fore.WHITE}• FakeKiller 9000 checks for Facebook security warnings during run.")
    print(f"\n{Fore.LIGHTBLACK_EX}© 2025 | FakeKiller 9000 – Vengeance Edition | Educational Use Only")
    print(f"\n{Fore.YELLOW}TL;DR: {Fore.WHITE}You use FakeKiller 9000 at your own risk. No support, no guarantees.")
    print(f"\n{Fore.LIGHTBLUE_EX}⏳ Please read the above carefully. Starting in:")
    for i in range(5, 0, -1):
        print(f"\r{Fore.LIGHTBLUE_EX}⏳ {i} seconds...", end='', flush=True)
        time.sleep(1)
    print()
    print(f"\n{Fore.CYAN}Do you accept all risks and wish to proceed?")
    print_option(1, "Yes, I understand and accept.")
    print_option(2, "No, exit FakeKiller 9000.")
    while True:
        choice = input(f"\n{Fore.CYAN}Enter your choice (1/2): {Style.RESET_ALL}").strip()
        if choice == "1":
            quick_success("Consent recorded.")
            return True
        elif choice == "2":
            quick_error("FakeKiller 9000 execution aborted by user.")
            return False
        else:
            quick_warning("Please enter a valid option: 1 or 2.")

def show_banner():
    print(f"{Fore.LIGHTMAGENTA_EX} █████▒▒███▀▀▀███▒▒█████▒▒███▄░░░   {Fore.CYAN}╔═══════════════════════════════╗")
    print(f"{Fore.LIGHTMAGENTA_EX}███▒▒▒▒▒███░░░███▒███░░█▒▒████▄░    {Fore.CYAN}║  {Fore.GREEN}FAKEKILLER 9000 - Vengeance  ║")
    print(f"{Fore.LIGHTMAGENTA_EX}███▒▒▒▒▒███░░░███▒██████▒▒██▒███    {Fore.CYAN}║  {Fore.YELLOW}AUTOMATED FB REPORT TOOL     ║")
    print(f"{Fore.LIGHTMAGENTA_EX}███▒▒▒▒▒███░░░███▒███░░█▒▒██░░██    {Fore.CYAN}║  {Fore.RED}USE AT YOUR OWN RISK ⚠️       ║")
    print(f"{Fore.LIGHTMAGENTA_EX}▒█████▒▒▀███▒▒███▒███░░█▒▒██░░░█    {Fore.CYAN}║  {Fore.CYAN}DEVELOPER: Ebn Hussein       ║")
    print(f"{Fore.LIGHTMAGENTA_EX}▒█████▒▒▀███▒▒███▒███░░█▒▒██░░░█    {Fore.CYAN}║  {Fore.BLUE}FB: fb.com/Ebnhusssein       ║")
    print(f"{Fore.LIGHTMAGENTA_EX}▒█████▒▒▀███▒▒███▒███░░█▒▒██░░░█    {Fore.CYAN}╚═══════════════════════════════╝")
    print(f"{Fore.BLUE}💀 INITIATING CYBER SURVEILLANCE...{Style.RESET_ALL}")

def main():
    try:
        log_result('N/A', 'info', 'setup', None, 'Starting script setup')
        setup_terminal()
        show_banner()
        if not show_disclaimer():
            log_result('N/A', 'failed', 'disclaimer', 'User did not accept disclaimer', 'User aborted at disclaimer')
            return
        log_result('N/A', 'success', 'disclaimer', None, 'User accepted disclaimer')
        quick_clear()
        quick_header("BROWSER MODE SELECTION")
        print_option(1, "Visible browser (see what's happening)")
        print_option(2, "Background mode (hidden browser)")
        while True:
            browser_mode_choice = input(f"\n{Fore.CYAN}Enter your choice (1/2): {Style.RESET_ALL}").strip()
            if browser_mode_choice in ["1", "2"]:
                break
            else:
                quick_error("Invalid choice. Please enter 1 or 2.")
        log_result('N/A', 'info', 'browser_mode', None, f'Selected: {"Visible" if browser_mode_choice=="1" else "Background"} browser mode')
        if browser_mode_choice == "1":
            headless_mode = False
            quick_success("Selected: Visible browser mode")
        else:
            headless_mode = True
            quick_success("Selected: Background mode")
        quick_clear()
        quick_header("REPORTING PARAMETERS")
        print_option(1, "Report as 'Me'")
        print_option(2, "Report as 'A friend'")
        while True:
            report_type_choice = input(f"\n{Fore.CYAN}Enter your choice (1/2): {Style.RESET_ALL}").strip()
            if report_type_choice in ["1", "2"]:
                break
            else:
                quick_error("Invalid choice. Please enter 1 or 2.")
        log_result('N/A', 'info', 'report_type', None, f'Selected: {"Me" if report_type_choice=="1" else "A friend"}')
        if report_type_choice == "1":
            report_type = "me"
            quick_success("Selected: Report as 'Me'")
        else:
            report_type = "friend"
            quick_success("Selected: Report as 'A friend'")
        print(f"\n⚠️  Maximum reports per profile: {MAX_REPORTS_PER_TARGET}")
        print(f"⚠️  It is safer not to report more than {SAFE_REPORT_LIMIT} times per account consecutively. ⚠️")
        while True:
            try:
                reports_per_account = int(input(f"How many reports should be sent per account? (1-{MAX_REPORTS_PER_TARGET}): ").strip())
                if 1 <= reports_per_account <= MAX_REPORTS_PER_TARGET:
                    quick_success(f"Selected: {reports_per_account} reports per account")
                    break
                else:
                    quick_error("Please enter a number within the valid range.")
            except ValueError:
                quick_error("Invalid number. Try again.")
        log_result('N/A', 'info', 'load_targets', None, 'Loading targets from file')
        try:
            with open(TARGETS_FILE, "r") as f:
                targets = [line.strip() for line in f if line.strip()]
            quick_success(f"Loaded {len(targets)} target profiles")
            log_result('N/A', 'success', 'load_targets', None, f'Loaded {len(targets)} targets')
        except FileNotFoundError:
            quick_error(f"Error: {TARGETS_FILE} not found!")
            log_result('N/A', 'failed', 'load_targets', f'{TARGETS_FILE} not found', 'Check targets.txt file')
            return
        except Exception as e:
            quick_error(f"Error reading targets file: {e}")
            log_result('N/A', 'failed', 'load_targets', str(e), 'Check targets.txt file')
            return
        if not targets:
            quick_error("No targets found in targets.txt file!")
            log_result('N/A', 'failed', 'load_targets', 'No targets found', 'Add targets to targets.txt')
            return
        total = len(targets) * reports_per_account
        quick_info(f"📊 Total reports to be sent: {total}")
        quick_header("STARTING EXECUTION")
        quick_info("All settings collected. Starting browser and execution...")
        log_result('N/A', 'info', 'browser_start', None, 'Starting browser and loading cookies')
        if not os.path.isfile(CHROMEDRIVER_BIN):
            success = download_chromedriver()
            if not success:
                quick_error("Cannot continue without ChromeDriver. Please install manually.")
                log_result('N/A', 'failed', 'browser_start', 'ChromeDriver missing', 'Install ChromeDriver')
                return
        options = Options()
        if headless_mode:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            quick_info("🔒 Browser will run in background mode")
        else:
            options.add_argument("--start-maximized")
            quick_info("👁️  Browser will be visible")
        service = Service(executable_path=CHROMEDRIVER_BIN)
        try:
            driver = webdriver.Chrome(service=service, options=options)
            quick_success("Browser started successfully")
            log_result('N/A', 'success', 'browser_start', None, 'Browser started')
        except Exception as e:
            quick_error(f"Failed to launch ChromeDriver: {e}")
            log_result('N/A', 'failed', 'browser_start', str(e), 'Check ChromeDriver installation')
            return
        quick_info("🔐 Loading cookies and checking login...")
        log_result('N/A', 'info', 'load_cookies', None, 'Loading cookies')
        load_cookies(driver, COOKIES_FILE)
        if not check_login(driver):
            quick_error("Login failed. Please check your cookies.")
            log_result('N/A', 'failed', 'login', 'Login failed', 'Check cookies.json')
            driver.quit()
            return
        log_result('N/A', 'success', 'login', None, 'Login successful')
        friend_identifier = None
        if report_type == "friend":
            log_result('N/A', 'info', 'extract_friend_id', None, 'Extracting friend identifier')
            try:
                with open(MY_PROFILE_FILE, "r") as f:
                    my_profile_url = f.read().strip()
                friend_identifier = extract_identifier_from_loaded_page(driver, my_profile_url)
                quick_info(f"🆔  Friend identifier: {friend_identifier}")
                log_result('N/A', 'success', 'extract_friend_id', None, f'Friend identifier: {friend_identifier}')
            except FileNotFoundError:
                quick_error(f"Error: {MY_PROFILE_FILE} not found!")
                log_result('N/A', 'failed', 'extract_friend_id', f'{MY_PROFILE_FILE} not found', 'Check my_friend_account.txt')
                driver.quit()
                return
        quick_header("STARTING REPORTS")
        quick_info("All reports will be sent to the selected profiles.")
        log_result('N/A', 'info', 'start_reports', None, 'Starting reports loop')
        current = 0
        for profile_url in targets:
            log_result(profile_url, 'info', 'target_start', None, f'Starting reports for target')
            print(f"\n🎯 Target profile: {profile_url}")
            for r in range(reports_per_account):
                current += 1
                quick_info(f"Report {r+1}/{reports_per_account} for this profile")
                log_result(profile_url, 'info', 'report_attempt', None, f'Starting report {r+1} of {reports_per_account}')
                if not check_facebook_security(driver):
                    quick_warning("Security issue detected, stopping...")
                    log_result(profile_url, 'failed', 'security_check', 'Facebook security check detected', 'Complete security check manually')
                    driver.quit()
                    return
                report_account(driver, profile_url, friend_identifier, report_type=report_type, fast=(r > 0))
                log_result(profile_url, 'success', 'report_attempt', None, f'Finished report {r+1} of {reports_per_account}')
            log_result(profile_url, 'success', 'target_end', None, f'Finished all reports for target')
        quick_success(f"Done! Sent {total} report(s) across {len(targets)} profile(s).")
        log_result('N/A', 'success', 'done', None, f'Sent {total} reports across {len(targets)} profiles')
        driver.quit()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  FakeKiller 9000 interrupted by you (Ctrl+C)")
        print(f"{Fore.CYAN}Exiting gracefully...{Style.RESET_ALL}")
        log_result('N/A', 'failed', 'interrupted', 'Interrupted by user', 'User pressed Ctrl+C')
        try:
            driver.quit()
        except:
            pass
        return
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}")
        print(f"{Fore.CYAN}FakeKiller 9000 will exit.{Style.RESET_ALL}")
        log_result('N/A', 'failed', 'exception', str(e), 'Unexpected error, check details')
        try:
            driver.quit()
        except:
            pass
        return

if __name__ == "__main__":
    main()



