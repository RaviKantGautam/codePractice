from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time


class Scrapy2:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        # self.driver = webdriver.Chrome(options=options)
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.file = open('diamonds.csv', 'a', newline='')
        header = ['Name', 'Price', 'Carat', 'Cut', 'Color', 'Clarity', 'Certificate', 'Table Size',
                  'Depth', 'Symmetry', 'Polish', 'Fluorescence', 'Measurements', 'Length', 'Width', 'Height']
        csv.writer(self.file).writerow(header)
        self.base_url = "https://www.brilliantearth.com/diamond/round/"

    def driver_config(self):
        self.driver.get(self.base_url)
        remove_filter = self.wait_for_element("filter_exposed_text")
        remove_filter.find_element(By.TAG_NAME, "a").click()
        return self.wait_for_element("diamonds_search_table")

    def wait_for_element(self, element):
        wait = WebDriverWait(self.driver, 10)
        return wait.until(EC.presence_of_element_located((By.ID, element)))

    def get_data(self):
        main_div = self.driver_config()
        time.sleep(5)
        inner_divs = main_div.find_elements(By.CSS_SELECTOR, ".inner.item")
        item_count = 0
        while len(inner_divs) - 1 > item_count:
            inner_divs[item_count].click()
            try:
                parsed_data = self.parse_data(
                    inner_divs[item_count].get_attribute('innerHTML'))
                print(parsed_data)
                self.write_to_csv(parsed_data)
                inner_divs[item_count].click()
                item_count += 1
                inner_divs = main_div.find_elements(
                    By.CSS_SELECTOR, ".inner.item")
                # if item_count == len(inner_divs) - 1:
                if item_count == 10:
                    break
            except Exception as e:
                print(e)
                item_count += 1
                continue
        return True

    def parse_data(self, html):
        try:
            bs = BeautifulSoup(html, 'html.parser')
            card = bs.find('div', {"class": 'table-diamond-detail'})
            name = card.find(
                'div', {'class': 'diamond-info-panel'}).find('p').text
            diamond_info = card.find_all('div', {'class': 'diamond-line-info'})
            price = diamond_info[0].find(
                'div', {'class': 'diamond-line-info-text'}).text.strip()
            carat = diamond_info[1].find(
                'div', {'class': 'diamond-line-info-text'}).text.strip()
            cut = diamond_info[2].find(
                'div', {'class': 'diamond-line-info-text'}).text.strip()
            color = diamond_info[3].find(
                'div', {'class': 'diamond-line-info-text'}).text.strip()
            clarity = diamond_info[4].find(
                'div', {'class': 'diamond-line-info-text'}).text.strip()
            additional_info = {}
            additional_detail = card.find_all('div', {'class': 'diamond-line-info'})[
                5].find('div', {'class': 'additonal-details-content'})
            for i in additional_detail.find_all('div', {'class': 'headline'}):
                key = i.text.strip()
                value = i.findNextSibling('div').text.strip()
                additional_info[key] = value

            extra_additional_detail = card.find_all('div', {'class': 'diamond-line-info'})[
                5].find('div', {'class': 'list-unstyled d-flex additonal-details-content'})
            for i in extra_additional_detail.find_all('div', {'class': 'headline'}):
                key = i.text.strip()
                value = i.findNextSibling('div').text.strip()
                additional_info[key] = value
        except Exception as e:
            print(e)
            print('Error')
            raise e
        return [name, price, carat, cut, color, clarity] + list(additional_info.values())

    def write_to_csv(self, data):
        writer = csv.writer(self.file)
        writer.writerow(data)

    def close_tab(self):
        self.driver.close()

    def __del__(self):
        self.driver.quit()


if __name__ == '__main__':
    s = Scrapy2()
    s.get_data()
    s.close_tab()
