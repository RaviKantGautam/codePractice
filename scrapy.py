from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time
import math
import pandas as pd
import time


class Scrapy:
    def __init__(self):
        # options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.result = []
        self.page = 1
        self.base_url = "https://www.brilliantearth.com/loose-diamonds/list/"

    def get_data(self, page=1):
        url = self.base_url + f"?page={page}"
        if page == 1:
            self.driver.get(url)
        self.driver.execute_script("window.open('{}', '_blank')".format(url))
        time.sleep(5)
        
        # Switch to the second tab
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # Perform your desired actions on the second tab
        # For example, you can get the page source
        page_source = self.driver.page_source
        while '{"diamonds' not in page_source:
            time.sleep(5)
            # x = random.randint(100, 1920)
            # y = random.randint(100, 1080)
            # duration = random.randint(1, 5)
            # pyautogui.moveRel(10, 0, duration=1)
            # pyautogui.moveTo(x, y, duration=duration)
            print("Retrying")
            page_source = self.driver.page_source

        soup = BeautifulSoup(page_source, 'html.parser')
        body = soup.find('body').text
        try:
            data = json.loads(body)
        except:
            print("Error")
            print("Data")
            print(body)
            data = {}
        
        self.close_tab()
        return data
    
    def close_tab(self):
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
    
    def get_all_data(self):
        data = self.get_data()
        total_pages = math.ceil(len(data['diamonds'])/int(data.get('total_pages', 1)))
        self.parse_data(data)
        if total_pages > 1:
            for i in range(2, total_pages):
                data = self.get_data(page=i)
                self.parse_data(data)
                if len(self.result) >= 1000:
                    break
    
    def parse_data(self, data):
        for i in range(len(data['diamonds'])):
            price = data['diamonds'][i]['price']
            carat  = data['diamonds'][i]['carat']
            color = data['diamonds'][i]['color']
            cut = data['diamonds'][i]['cut']
            clarity = data['diamonds'][i]['clarity']
            shape = data['diamonds'][i]['shape']
            measurements = data['diamonds'][i]['measurements']
            report = data['diamonds'][i]['report']
            depth = data['diamonds'][i]['depth']
            table = data['diamonds'][i]['table'] 
            origin = data['diamonds'][i]['origin']
            symmetry = data['diamonds'][i]['symmetry']
            flour = data['diamonds'][i]['fluorescence']
            polish = data['diamonds'][i]['polish']
            culet = data['diamonds'][i]['culet']
            girdle = data['diamonds'][i]['girdle']
            length_width_ratio = data['diamonds'][i]['length_width_ratio']

            self.result.append([price, carat, color, cut, clarity, shape, measurements, report, depth, table, origin, symmetry, flour, polish, culet, girdle, length_width_ratio])
        
        return self.result
    
    def run(self):
        self.get_all_data()
        column = ['price', 'carat', 'color', 'cut', 'clarity', 'shape', 'measurements', 'report', 'depth', 'table', 'origin', 'symmetry', 'fluorescence', 'polish', 'culet', 'girdle', 'length_width_ratio']
        pd.DataFrame(self.result, columns=column).to_csv("diamonds.csv")
        print("Data Saved")
        return self.result
    
    def close(self):
        self.driver.quit()

if __name__ == "__main__":
    scrapy = Scrapy()
    result = scrapy.run()
    print(result)
    scrapy.close()

