from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from prettytable import PrettyTable

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
            "//*[@id='job_list_table']/tbody/tr"
        )
        return rows

    def get_data_from_rows(self,args1,args2):
        # data = {}
        datalist=[]
        id = 1
        rows = self.get_table_rows()
        for row in rows[5:]:
            title = row.find_element(
                By.XPATH,
                "./td[2]/a[1]"
                ).get_attribute("innerHTML")

            for inc in args1:
                for excl in args2:
                    if inc in title:
                        if excl not in title:
                            url = row.find_element(
                                By.XPATH,
                                "./td[2]/a[1]"
                                ).get_attribute("href")
                            company = row.find_element(
                                By.XPATH,
                                "./td[4]/a[1]"
                                ).get_attribute("innerHTML")
                            published = row.find_element(
                                By.XPATH,
                                "./td[5]"
                                ).get_attribute("innerHTML")
                            last_date = row.find_element(
                                By.XPATH,
                                "./td[6]"
                                ).get_attribute("innerHTML")
                            
                            datalist.append(
                                [id,
                                title.strip(),
                                company.replace('\t','').replace('\n',''),
                                url,
                                published,
                                last_date.replace('\t','').replace('\n','')]
                            )
                            id+=1
        return datalist

    def report(self,args1,args2):
        datalist = self.get_data_from_rows(args1,args2)

        # create table columns
        columns = ['ID','Job Title','Company','URL','Publish Date','End Date']
        table = PrettyTable(
            field_names=columns
        )
        table.add_rows(datalist)
        print(table)