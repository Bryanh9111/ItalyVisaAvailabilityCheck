# Importing required modules
import requests
import schedule
import time
import redis
import json
import logging
import random
import threading
from requests.exceptions import RequestException, Timeout
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from datetime import datetime, timedelta, date
# Importing configurations
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_COOKIE_CHANNEL, REDIS_TIME_CHANNEL
from config import FILE_PATH_SELENIUM, FILE_NAME_PREFIX_SELENIUM
from config import CHROME_DRIVER_PATH
from config import NAVIGATION_URL, USER_NAME, PASSWORD


class BrowserAutomator:
    # Initialize browser automator with a driver path
    def __init__(self, driver_path):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.driver = webdriver.Chrome(executable_path=driver_path)

    # Navigate to a specified URL
    def navigate_to_page(self, url):
        try:
            self.driver.get(url)
        except Exception as e:
            print(f"Exception occurred while trying to navigate to {url}: {e}")
            self.logger.error(f"Exception occurred while trying to navigate to {url}: {e}")
            raise

    # Click an element on the webpage
    def click_element(self, element_type, element_identifier, wait_time=15):
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((element_type, element_identifier)))
            element.click()
        except NoSuchElementException as e:
            print("No Such Element Exception! The element you were trying to reach could not be found.")
            self.logger.error(f"No Such Element Exception: {e}")
        except TimeoutException as e:
            print("Timeout Exception! Element not found or page took too long to load.")
            self.logger.error(f"Timeout Exception! Element not found or page took too long to load: {e}")
            raise

    # Click Checkbox on the webpage
    def check_checkbox(self, element_type, element_identifier, wait_time=10, clickEnter=False):
        try:
            checkbox = WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((element_type, element_identifier)))
            #if not checkbox.is_selected():
            checkbox.click()
            if clickEnter:
                checkbox.send_keys(Keys.RETURN)
        except NoSuchElementException as e:
            print("No Such Element Exception! The element you were trying to reach could not be found.")
            self.logger.error(f"No Such Element Exception: {e}")
        except TimeoutException as e:
            print("Timeout Exception! Element not found or page took too long to load.")
            self.logger.error(f"Timeout Exception! Element not found or page took too long to load: {e}")
            raise

    # Click an element on the webpage
    def send_keys_to_element(self, element_type, element_identifier, keys, wait_time=15, clickEnter=False):
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((element_type, element_identifier)))
            element.clear()
            element.send_keys(keys)
            if clickEnter:
                element.send_keys(Keys.RETURN)
        except NoSuchElementException as e:
            print("No Such Element Exception! The element you were trying to reach could not be found.")
            self.logger.error(f"No Such Element Exception: {e}")
        except TimeoutException as e:
            print("Timeout Exception! Element not found or page took too long to load.")
            self.logger.error(f"Timeout Exception! Element not found or page took too long to load: {e}")
            raise

    # Accept the Alert box on the webpage
    def accept_alert(self, wait_time=10):
        try:
            WebDriverWait(self.driver, wait_time).until(EC.alert_is_present())
            alert = Alert(self.driver)
            alert.accept()
        except TimeoutException as e:
            print("Timeout Exception! Alert not found or took too long to appear.")
            self.logger.error(f"Timeout Exception! Alert not found or took too long to appear: {e}")
        except NoAlertPresentException as e:
            print("No Alert Present Exception! No alert is currently present.")
            self.logger.error(f"No Alert Present Exception: {e}")
            raise

    #Close the browser instance connection
    def close_browser(self, seconds):
        time.sleep(20)
        try:
            self.driver.quit()
        except Exception as e:
            print(f"An error occurred while close_browser: {e}")
            self.logger.error(f"An error occurred while close_browser: {e}")

    #Get all the cookies from request header
    def get_all_cookies(self):
        return self.driver.get_cookies()


class APIClient:
    # Initialize API client with a base URL
    def __init__(self, base_url):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.base_url = base_url

    # Get cookies from a specified endpoint
    def get_cookies(self, endpoint):
        try:
            response = requests.get(self.base_url + endpoint, timeout=10)
            response.raise_for_status()
        except Timeout as e:
            print("Timeout Error! The request took too long to complete.")
            self.logger.error(f"Timeout Error: {e}")
            return None
        except RequestException as e:
            print(f"Request Error! An error occurred: {e}")
            self.logger.error(f"Request Error: {e}")
            return None

        return response.cookies


class RedisSvc:
    # Initialize RedisPublisher
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        try:
            self.r = redis.Redis(host=host, port=port, db=db)
            self.r.ping()
        except redis.ConnectionError as e:
            print("Cannot connect to Redis server. Please make sure the server is running and the host and port are correct.")
            self.logger.error(f"An error occurred: {e}")
            raise

    # Publisher
    def send_message(self, channel, message):
        try:
            message_json = json.dumps(message)
            self.r.publish(channel, message_json)
        except redis.RedisError as e:
            print(f"An error occurred when publishing a message: {e}")
            self.logger.error(f"An error occurred when publishing a message: {e}")
            raise

    # Subscriber
    def receive_message(self, channel):
        try:
            pubsub = self.r.pubsub()
            pubsub.subscribe(channel)

            while True:
                message = pubsub.get_message()
                if message and message['type'] == 'message':
                    message_data = json.loads(message['data'])
                    # print(f"Received message: {message_data}")
                    return message_data
                else:
                    time.sleep(1)
        except redis.RedisError as e:
            print(f"An error occurred when receiving a message: {e}")
            self.logger.error(f"An error occurred when receiving a message: {e}")
            raise


class ScheduleJob:
    # Initialize ScheduleJob with chromedriver
    def __init__(self, redisSvc: RedisSvc, driver_path):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        #self.browser = browser
        self.redisSvc = redisSvc
        self.driver_path = driver_path
        # Start a new thread to listen to the Redis channel for messages
        self.redis_thread = threading.Thread(target=self.checkTrigger)
        self.redis_thread.daemon = True
        self.redis_thread.start()

    # Redis Subscriber to run job
    def checkTrigger(self):
        try:
            while True:
                message = self.redisSvc.receive_message(REDIS_TIME_CHANNEL)
                if message:
                    need_to_run = message.get('run')
                    if need_to_run:
                        print('Received run flag, running job immediately!!!!')
                        if self.browser:
                            self.browser.close_browser(1)
                        schedule.clear()  # Clear the current schedule
                        self.run()  # Run the schedule again
        except Exception as e:
            print(f"An error occurred while checkTrigger: {e}")
            self.logger.error(f"An error occurred while checkTrigger: {e}")

    # Create web automation job for running
    def job(self, interval):
        try:
            self.logger.info(f'job started: {datetime.now()}')
            self.browser = BrowserAutomator(self.driver_path)  # create a new instance for each job run
            self.browser.navigate_to_page(NAVIGATION_URL)
            self.browser.send_keys_to_element(By.NAME, 'Email', USER_NAME, 60)
            self.browser.send_keys_to_element(By.NAME, 'Password', PASSWORD, wait_time=60, clickEnter=True)
            self.browser.click_element(By.ID, 'advanced', 120)
            self.browser.click_element(By.XPATH, '//a[@href="/Services/Booking/2354"]', 120)
            self.browser.check_checkbox(By.ID, 'PrivacyCheck', 80, clickEnter=True)
            self.browser.accept_alert()
            cookies = self.browser.get_all_cookies()
            next_run_time = (datetime.now() + timedelta(minutes=interval) + timedelta(seconds=20)).strftime("%Y-%m-%d %H:%M:%S")
            if (len(cookies) > 0):
                cookie_to_send = "; ".join([f'{cookie["name"]}={cookie["value"]}' for cookie in reversed(cookies)])
                cookie_to_send = cookie_to_send.strip()
                self.redisSvc.send_message(REDIS_COOKIE_CHANNEL, {'cookie': cookie_to_send, 'next_run_time': next_run_time})
            else:
                self.redisSvc.send_message(REDIS_COOKIE_CHANNEL, {'cookie': '-1'})

            print(f'next run time: {next_run_time}')
            self.browser.close_browser(5)
        except Exception as e:
            print(f"An error occurred while running job: {e}")
            self.logger.error(f"An error occurred while running job: {e}")
            self.redisSvc.send_message(REDIS_COOKIE_CHANNEL, {'cookie': '-1'})
            if self.browser:
                self.browser.close_browser(5)
            time.sleep(120)
            schedule.clear()  # Clear the current schedule
            self.run()  # Run the schedule again

    # running the job in a timely manner
    def run(self):
        #generate a randon interval
        interval = random.randint(15, 20)
        self.job(interval)
        #schedule.every(interval).minutes.do(self.job)
        schedule.every(interval).minutes.do(lambda: self.job(interval))
        while True:
            try:
                schedule.run_pending()
            except Exception as e:
                print(f"An error occurred while running schedule: {e}")
                self.logger.error(f"An error occurred while running schedule: {e}")
            time.sleep(1)


if __name__ == "__main__":
    # Initialize global variables
    filePath = FILE_PATH_SELENIUM
    fileNamePrefix = FILE_NAME_PREFIX_SELENIUM
    fileSuffix = date.today().strftime("%Y-%m-%d")

    # Configure the logger
    logging.basicConfig(filename=rf'{filePath}\{fileNamePrefix}-log-{fileSuffix}.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    #browser = BrowserAutomator(CHROME_DRIVER_PATH)

    # Create an instance of RedisPublisher
    redisSvc = RedisSvc()

    # Create an instance of ScheduleJob
    scheduled_job = ScheduleJob(redisSvc, CHROME_DRIVER_PATH)

    # Run the scheduled job
    scheduled_job.run()



    # api_client = APIClient('https://prenotami.esteri.it')
    # cookies = api_client.get_cookies('/Services/RetrieveServices')
    # for cookie in cookies:
    #     print(f'Name: {cookie.name}, Value: {cookie.value}')

    #browser.close_browser(20)