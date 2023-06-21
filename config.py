# config.py
import json

# Load Credentials
def load_credentials():
    with open('VisaAvailabilityCheckCredentials.json', 'r') as file:
        credentials = json.load(file)
    return credentials

CREDENTIALS = load_credentials()

#Redis configs
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_COOKIE_CHANNEL = 'visa_cookie_channel'
REDIS_TIME_CHANNEL = 'visa_time_channel'

#File configs
FILE_PATH = r'C:\Users\zhhlb\OneDrive\桌面'
FILE_NAME_PREFIX = 'VisaDates'
DELETE_FILE_IN_DAYS = 1

#Email configs
EMAIL_SERVER = 'smtp-mail.outlook.com'  # SMTP server
EMAIL_PORT = 587  # SMTP port
EMAIL_USER = CREDENTIALS["EMAIL_USER"]  # Your email address "zhhlbaw2011@outlook.com"  ""zhhlbaw2016@outlook.com""
EMAIL_PASSWORD = CREDENTIALS["EMAIL_PASSWORD"]  # Your email password
RECIPIENTS = ["zhhlbaw2011@gmail.com", "liu555yang@gmail.com"]  # Recipient email address ["zhhlbaw2011@gmail.com", "hzhou55@asu.edu"]

#API configs
API_URL = 'https://prenotami.esteri.it/BookingCalendar/RetrieveCalendarAvailability'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
SERVICE_ID = '2354'
NUM_MONTHS_TO_FETCH = 4
API_SCHEDULE = 1 #Call api every {} minutes

#WebAutomation file configs
FILE_PATH_SELENIUM = r'C:\Users\zhhlb\OneDrive\桌面'
FILE_NAME_PREFIX_SELENIUM = 'VisaDates-Selenium'

#WebAutomation chrome driver configs
CHROME_DRIVER_PATH = r'E:\pys\wangyi_web_crawler\ChromeDriver\chromedriver.exe'

#WebAutomation configs
NAVIGATION_URL = 'https://prenotami.esteri.it/'
USER_NAME = CREDENTIALS["USER_NAME"]
PASSWORD = CREDENTIALS["PASSWORD"]