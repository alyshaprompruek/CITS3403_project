

import time
import uuid
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

BASE_URL = "http://localhost:5000"

def generate_unique_email():
    return f"testuser_{uuid.uuid4().hex[:6]}@test.com"

@pytest.mark.usefixtures("driver")
def test_s01_signup_success(driver):
    email = generate_unique_email()
    password = "Test1234$"

    driver.get(f"{BASE_URL}/signup")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    time.sleep(1)
    assert "dashboard" in driver.current_url.lower()

def test_s02_login_failure(driver):
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.NAME, "email").send_keys("wrong@example.com")
    driver.find_element(By.NAME, "password").send_keys("WrongPass123$")
    driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    time.sleep(1)
    error = driver.find_element(By.CLASS_NAME, "alert-danger")
    assert "invalid" in error.text.lower()

def test_s03_add_unit(driver):
    # Login first
    driver.get(f"{BASE_URL}/login")
    driver.find_element(By.NAME, "email").send_keys("testuser@example.com")
    driver.find_element(By.NAME, "password").send_keys("Test1234$")
    driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    time.sleep(1)
    driver.get(f"{BASE_URL}/track_grades")

    # Fill Unit form
    driver.find_element(By.NAME, "name").send_keys("Test Unit")
    driver.find_element(By.NAME, "unit_code").send_keys("CITS1234")
    driver.find_element(By.NAME, "semester").send_keys("1")
    driver.find_element(By.NAME, "year").send_keys("2025")
    driver.find_element(By.NAME, "target_score").send_keys("80")
    driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    time.sleep(1)
    page_source = driver.page_source
    assert "CITS1234" in page_source

def test_s04_add_task(driver):
    driver.get(f"{BASE_URL}/track_grades")
    driver.find_element(By.CSS_SELECTOR, "button[data-bs-target='#taskModal']").click()
    time.sleep(1)

    driver.find_element(By.NAME, "task_name").send_keys("Midterm")
    driver.find_element(By.NAME, "type").send_keys("assignment")
    driver.find_element(By.NAME, "score").send_keys("85")
    driver.find_element(By.NAME, "weight").send_keys("30")
    driver.find_element(By.NAME, "date").send_keys("2025-06-01")
    driver.find_element(By.NAME, "note").send_keys("Auto test")

    driver.find_element(By.CSS_SELECTOR, "#taskModal button[type='submit']").click()
    time.sleep(2)

    assert "Midterm" in driver.page_source

def test_s05_delete_unit(driver):
    driver.get(f"{BASE_URL}/track_grades")
    delete_buttons = driver.find_elements(By.CSS_SELECTOR, "form[action='/delete_unit'] button")
    if delete_buttons:
        delete_buttons[0].click()
        time.sleep(2)
        assert "CITS1234" not in driver.page_source
    else:
        pytest.skip("No unit found to delete.")

def test_s06_sharing_unauthorized_access(driver):
    invalid_token = "invalidtoken123"
    driver.get(f"{BASE_URL}/share/view/{invalid_token}")
    time.sleep(1)
    assert "you do not have permission" in driver.page_source.lower() or "unauthorized" in driver.page_source.lower()