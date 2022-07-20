from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
# PATH = "~/.webdriver/chromedriver"

class Jobs(webdriver.Chrome):
    def __init__(self,teardown=True):
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36"

        self.teardown = teardown
        options = Options()
        options.headless = True
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        service = Service(ChromeDriverManager().install())

        super(Jobs,self).__init__(
            service=service,
            options=options
        )
        self.implicitly_wait(5)
        self.maximize_window()
        print("Hello there, This is a jobs.ge bot")

    def __exit__(self,exc_type, exc_val,exc_tb):
        if self.teardown:
            self.quit()

    def land_first_page(self):
        self.get("https://jobs.ge/")

    def change_category(self):
        category = self.find_element(
            By.XPATH, 
            "//select/option[@value='6']"
        )
        category.click()

    def get_table_rows(self):
        rows = self.find_elements(
            By.XPATH,
            # "//div[@style='margin-top:5px;']/table/tbody/tr"
            "//*[@id='job_list_table']/tbody/tr"
        )
        return rows

    def get_data_from_rows(self):
        data = {}
        rows = self.get_table_rows()
        for row in rows[5:]:
            url = row.find_element(
                By.XPATH,
                # "./td[2]/a/text()"
                "./td[2]/a[1]"
            ).get_attribute("href")
            title = row.find_element(
                By.XPATH,
                "./td[2]/a[1]"
            ).get_attribute("innerHTML")
            data['title'] = title
            data['url'] = url 


