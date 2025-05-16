# testing/selenium/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

@pytest.fixture(scope="session")
def driver():
    options = Options()
    # options.add_argument("--headless")  # Uncomment this line to run Chrome in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service()  # Specify the path to your ChromeDriver if not in PATH
    driver = webdriver.Chrome(service=service, options=options)
    
    yield driver
    driver.quit()