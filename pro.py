from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import requests
import json

# ClickUp API credentials
CLICKUP_API_TOKEN = 'pk_4357977_XHXIN73RLJ0HCHVKB7VQ2ISKF80P7FNX'
CLICKUP_LIST_ID = '901406017711'  # Updated to the new List ID you provided

# API headers for authentication
headers = {
    'Authorization': CLICKUP_API_TOKEN,
    'Content-Type': 'application/json'
}

def create_clickup_task(task_name, task_description):
    url = f'https://api.clickup.com/api/v2/list/{CLICKUP_LIST_ID}/task'
    
    task_data = {
        'name': task_name,
        'description': task_description,
        'status': 'MISSED CALLS',
        'priority': 3,
        'notify_all': True,
        'tags': ['Inbound Lead'],
        'check_required_custom_fields': True
    }
    
    response = requests.post(url, json=task_data, headers=headers)
    
    if response.status_code == 200 or response.status_code == 201:
        print(f"Task '{task_name}' created successfully in ClickUp!")
    else:
        print(f"Failed to create task. Status Code: {response.status_code}, Response: {response.text}")

# Set up the WebDriver with options
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--no-sandbox")  # Necessary for running in Render or other cloud platforms
options.add_argument("--disable-dev-shm-usage")  # Helps reduce memory problems
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--incognito")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.implicitly_wait(20)

def login_manually():
    driver.get("https://app.prospectx.com/ca/")
    input("Please log in manually and press Enter once you have successfully logged in...")

def navigate_to_communications():
    driver.get("https://app.prospectx.com/cb/reports/communications")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

def filter_by_date():
    try:
        date_filter = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input.form-control.input-class"))
        )
        date_filter.click()

        time.sleep(2)

        last_7_days_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Yesterday')]"))
        )
        last_7_days_option.click()

        apply_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Apply')]"))
        )
        apply_button.click()

        time.sleep(4)
    except Exception as e:
        print(f"Error while selecting the date range: {e}")

def filter_by_direction():
    print("Please select the 'Inbound' filter manually now. The script will wait for 5 seconds...")
    time.sleep(5)
    print("Continuing with data extraction...")

def extract_data():
    data = []
    try:
        table = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "table"))
        )
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            cols = row.find_elements(By.CSS_SELECTOR, "td")
            call_data = [col.text for col in cols]
            data.append(call_data)

            # Updated task creation to include opportunity first
            task_name = f"Inbound Lead: {call_data[6]} - {call_data[0]}"  # Opportunity - From
            task_description = f"Opportunity: {call_data[6]}\nFrom: {call_data[0]}\nTo: {call_data[1]}\nDate: {call_data[2]}\nDirection: {call_data[3]}\nDuration: {call_data[4]}"
            create_clickup_task(task_name, task_description)

    except Exception as e:
        print(f"Error extracting data: {e}")
    
    return data

def save_data_to_csv(data):
    headers = [
        "From", "To", "Date", "Direction", "Duration",
        "Recording", "Opportunity", "Action"
    ]
    
    with open("communications_weekly_report.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)

def main():
    login_manually()
    navigate_to_communications()

    filter_by_date()
    filter_by_direction()

    data = extract_data()
    print("Done reading 1st page, waiting for 5 seconds...")
    time.sleep(5)

    driver.find_element(By.XPATH, "//a[text()='2']").click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
    data += extract_data()
    print("Done reading 2nd page, waiting for 5 seconds...")
    time.sleep(5)

    save_data_to_csv(data)
    driver.quit()

if __name__ == "__main__":
    main()