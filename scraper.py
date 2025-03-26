from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import re

# === CONFIG ===
EMAIL = "your@domain.bg"
PASSWORD = "password"
ROUNDCUBE_URL = "http://your.URL.com/roundcube"

START_PAGE = 1 # change the page if needed
MAX_PAGES = 80 # change the page if needed

# === BROWSER SETUP ===
options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--ignore-certificate-errors")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


# === SCRAPER FUNCTION ===
def extract_emails_on_current_page(page_num):
    print(f"\n📄 Scraping Page {page_num}...")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "messagelist")))
    time.sleep(2)

    all_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message")
    giftlab_emails = [el for el in all_emails if "giftlab" in el.text.lower()]
    print(f"🎯 Found {len(giftlab_emails)} Giftlab emails on page {page_num}.")

    collected_data = []

    for idx, _ in enumerate(giftlab_emails):
        try:
            giftlab_emails = driver.find_elements(By.CSS_SELECTOR, "tr.message")
            filtered_emails = [el for el in giftlab_emails if "giftlab" in el.text.lower()]
            giftlab_email = filtered_emails[idx]

            print(f"\n🔍 Opening email #{idx + 1} on page {page_num}:")
            print(giftlab_email.text.strip()[:100])

            giftlab_email.click()
            time.sleep(2)

            # ✅ Try iframe method
            try:
                WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "messagecontframe"))
                )
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "rcmBody"))
                )
                email_body = driver.find_element(By.CLASS_NAME, "rcmBody").text.strip()
                driver.switch_to.default_content()
            except Exception:
                print("⚠️ iframe failed — trying fallback method...")
                driver.switch_to.default_content()
                try:
                    email_body = driver.find_element(By.ID, "layout-content").text.strip()
                except:
                    print("❌ Could not extract email body. Skipping this email.")
                    continue

            # ✅ Extract contact info
            lines = [line.strip() for line in email_body.splitlines() if line.strip()]
            found_name = found_phone = found_email = None

            for line in lines:
                if not found_name and re.match(r"^[А-ЯA-Z][а-яa-z]+ [А-ЯA-Z][а-яa-z]+$", line):
                    found_name = line
                if not found_name and line.lower().startswith("име:"):
                    found_name = line.split(":", 1)[1].strip()
                if not found_phone and re.search(r"\b08[789]\d{7}\b", line):
                    found_phone = re.search(r"\b08[789]\d{7}\b", line).group(0)
                if not found_email and re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line):
                    found_email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", line).group(0)

            if found_phone or found_email:
                print(f"👤 Name: {found_name if found_name else 'Not found'}")
                print(f"📱 Phone: {found_phone if found_phone else 'Not found'}")
                print(f"✉️ Email: {found_email if found_email else 'Not found'}")

                collected_data.append({
                    "Name": found_name if found_name else "Not found",
                    "Phone": found_phone if found_phone else "Not found",
                    "Email": found_email if found_email else "Not found"
                })
            else:
                print("⚠️ Skipping email: no useful contact info found.")

            driver.back()
            time.sleep(2)

        except Exception as e:
            print(f"⚠️ Failed to process email #{idx + 1} on page {page_num}: {e}")
            driver.save_screenshot(f"error_email_page{page_num}_{idx + 1}.png")

    if collected_data:
        df = pd.DataFrame(collected_data)
        filename = f"giftlab_page_{page_num}.xlsx"
        df.to_excel(filename, index=False)
        print(f"💾 Saved page {page_num} data to {filename}")
    else:
        print(f"📭 No data to save on page {page_num}.")


# === LOGIN + START ===
try:
    driver.get(ROUNDCUBE_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "_user")))
    driver.find_element(By.NAME, "_user").send_keys(EMAIL)
    driver.find_element(By.NAME, "_pass").send_keys(PASSWORD)
    driver.find_element(By.NAME, "_pass").send_keys(Keys.RETURN)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "messagelist")))
    time.sleep(3)

    # 🔁 SKIP to START_PAGE
    if START_PAGE > 1:
        print(f"⏩ Skipping to page {START_PAGE}...")
        for _ in range(1, START_PAGE):
            try:
                next_button = driver.find_element(By.ID, "rcmbtn119")
                is_disabled = next_button.get_attribute("aria-disabled")

                if is_disabled == "false":
                    next_button.click()
                    time.sleep(4)
                else:
                    print("⛔ Can't go forward. Reached end of pagination early.")
                    break
            except Exception as e:
                print(f"❌ Error navigating to page {START_PAGE}: {e}")
                break

    # 🚀 SCRAPE LOOP
    current_page = START_PAGE
    while current_page <= MAX_PAGES:
        extract_emails_on_current_page(current_page)

        try:
            next_button = driver.find_element(By.ID, "rcmbtn119")
            is_disabled = next_button.get_attribute("aria-disabled")

            if is_disabled == "false":
                print("➡️ Going to next page...")
                next_button.click()
                current_page += 1
                time.sleep(4)
            else:
                print("⏹ No more pages left.")
                break
        except Exception as e:
            print(f"❌ Pagination error: {e}")
            break

finally:
    driver.quit()
