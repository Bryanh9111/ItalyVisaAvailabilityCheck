# Importing required modules
import requests
import os
import glob
import platform
import schedule
import redis
import time
import json
import threading
import logging
import smtplib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Importing configurations
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_COOKIE_CHANNEL, REDIS_TIME_CHANNEL
from config import FILE_PATH, FILE_NAME_PREFIX, DELETE_FILE_IN_DAYS
from config import API_URL, USER_AGENT, SERVICE_ID, NUM_MONTHS_TO_FETCH, API_SCHEDULE
from config import EMAIL_SERVER, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, RECIPIENTS, EXCEPTION_RECIPIENTS


class VisaAvailability:
    # Initialize VisaAvailability
    def __init__(self, url, headers, service_id, num_months, filePath, fileNamePrefix, fileSuffix, email_server, email_port, email_user, email_password, recipient_emails, exception_recipient_emails):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.url = url
        self.headers = headers
        self.service_id = service_id
        self.num_months = num_months
        self.filePath = filePath
        self.fileNamePrefix = fileNamePrefix
        self.fileSuffix = fileSuffix
        self.emailLocal = EmailLocal(email_server, email_port, email_user, email_password, recipient_emails, exception_recipient_emails)
        self.exceptionLst = []
        #self.session = requests.Session()
        self.next_run_time_str = ''
        self.redisSvc = RedisSvc()
        self.redis_cookie_channel = REDIS_COOKIE_CHANNEL
        self.redis_time_channel = REDIS_TIME_CHANNEL
        # Start a new thread to listen to the Redis channel for messages
        self.redis_thread = threading.Thread(target=self.update_cookie_from_redis)
        self.redis_thread.daemon = True
        self.redis_thread.start()

        #Create a memo dic for record sending notification email count
        self.memo = {}

    # Redis Subscriber update latest cookie
    def update_cookie_from_redis(self):
        try:
            while True:
                message = self.redisSvc.receive_message(self.redis_cookie_channel)
                if message:
                    cookie = message.get('cookie')
                    next_run_time = message.get('next_run_time')
                    #cookie = cookie.decode('utf-8')
                    if cookie:
                        print('Cookie received!!!!')
                        if(cookie == '-1'):
                            print(f'Cookie: {cookie}')
                        self.headers['Cookie'] = '' if cookie == '-1' else cookie

                    if next_run_time:
                        print(f'Next_run_time received: {next_run_time}')
                        self.next_run_time_str = next_run_time
                    else:
                        self.next_run_time_str = ''
        except Exception as e:
            print(f"An error occurred while update_cookie_from_redis: {e}")
            self.logger.error(f"An error occurred while update_cookie_from_redis: {e}")

    #Generate params for API call
    def get_parameters(self):
        try:
            today = datetime.today()
            start_date = datetime(today.year, today.month, 1)
            params = []
            for month_offset in range(self.num_months):
                current_date = start_date + relativedelta(months=month_offset)
                current_date_str = current_date.strftime('%Y-%m-01')
                param = {
                    'selectedDay': current_date_str,
                    '_Servizio': self.service_id
                }
                params.append(param)
            return params
        except Exception as e:
            print(f"An error occurred while get_parameters: {e}")
            self.logger.error(f"An error occurred while get_parameters: {e}")
            return []

    # Main logic here, check the Italy visa availability
    def get_availability(self, params):
        print('-' * 60)
        # No cookie received, no need to run
        if(len(self.headers['Cookie']) == 0):
            print(f"Cookie is empty!")
            self.logger.info(f"Cookie is empty!")
            return

        # For sending email use
        messageLst = []

        with open(rf'{self.filePath}\{self.fileNamePrefix}-{self.fileSuffix}.txt', 'a',encoding='utf8') as f:
            f.write(f"{'-' * 30}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{'-' * 30}" + '\n')

        for param in params:
            try:
                date_string = param["selectedDay"]
                date_object = datetime.strptime(date_string, "%Y-%m-%d")
                year = date_object.year
                month = date_object.month
                #######test exception#######
                # next_run_time_selenium = datetime.strptime(self.next_run_time_str, "%Y-%m-%d %H:%M:%S")
                # current_time = datetime.now()
                # time_difference = next_run_time_selenium - current_time
                # if time_difference > timedelta(minutes=8) and time_difference < timedelta(minutes=10):
                #     self.headers['Cookie'] = ''
                #######
                result = requests.post(self.url, params=param, headers=self.headers).text
                #result = self.session.post(self.url, params=param, headers=self.headers).text
                resultJson = json.loads(result)
                dic_resultJson = json.loads(resultJson)
                print(f'{len(dic_resultJson)} dates in {year}-{month}')
                #dic_resultJson[0]['SlotLiberi'] = 1  # test sending email
                for entry in dic_resultJson:
                    date_string = entry['DateLibere']
                    date = datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S")
                    formatted_date = date.strftime("%Y-%m-%d")
                    # Update the memo dictionary if the date in not a key
                    if formatted_date not in self.memo:
                        self.memo[formatted_date] = 0

                    if entry['SlotLiberi'] > 0:
                        print("slot found!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        slot_word = "slot" if entry['SlotLiberi'] == 1 else "slots"
                        self.memo[formatted_date] += 1
                        if self.memo[formatted_date] <= 2:
                            messageLst.append(f"{entry['SlotLiberi']} {slot_word} available on {formatted_date}!")
                        with open(rf'{self.filePath}\{self.fileNamePrefix}-{self.fileSuffix}.txt', 'a',
                                  encoding='utf8') as f:
                            f.write(f"slot found!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! + '\n' + {entry['SlotLiberi']} slots on {formatted_date}" + '\n')
            except Exception as e:
                print(f"An error occurred while get_availability: {e}")
                self.logger.error(f"An error occurred while get_availability: {e}")
                self.exceptionLst.append(f"An error occurred while get_availability: {e}")
                self.headers['Cookie'] = ''
                # publish an event in another channel to selenium bot
                if self.next_run_time_str:
                    next_run_time_selenium = datetime.strptime(self.next_run_time_str, "%Y-%m-%d %H:%M:%S")
                    current_time = datetime.now()
                    time_difference = next_run_time_selenium - current_time
                    if time_difference > timedelta(minutes=5):
                        self.redisSvc.send_message(self.redis_time_channel, {'run': 1})

        if(len(messageLst) > 0):
            message = "\n".join(messageLst)
            self.emailLocal.send_email(f"{message}", False)
        if(len(self.exceptionLst) > 0):
            message = "\n".join(self.exceptionLst)
            self.emailLocal.send_email(f"{message}", True)
            self.exceptionLst = []


class FileLocal:
    # Initialize FileLocal
    def __init__(self, filePath, fileNamePrefix):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.filePath = filePath
        self.fileNamePrefix = fileNamePrefix

    # Get the creation date of a file
    def creation_date(self, path_to_file):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                return stat.st_mtime

    # Delete old files
    def clean_old_files(self, days=1):
        days_ago = datetime.now() - timedelta(days=days)
        try:
            for file_name in glob.glob(os.path.join(self.filePath, f"{self.fileNamePrefix}*.log")):
                file_date = datetime.fromtimestamp(self.creation_date(file_name))
                if file_date.date() <= days_ago.date():
                    os.remove(file_name)
            for file_name in glob.glob(os.path.join(self.filePath, f"{self.fileNamePrefix}*.txt")):
                file_date = datetime.fromtimestamp(self.creation_date(file_name))
                if file_date.date() <= days_ago.date():
                    os.remove(file_name)
        except Exception as e:
            print(f"An error occurred while cleaning old files: {e}")
            self.logger.error(f"An error occurred while cleaning old files: {e}")


class EmailLocal:
    # Initialize EmailLocal
    def __init__(self, email_server, email_port, email_user, email_password, recipient_emails, exception_recipient_emails):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.email_server = email_server
        self.email_port = email_port
        self.email_user = email_user
        self.email_password = email_password
        self.recipient_emails = recipient_emails
        self.exception_recipient_emails = exception_recipient_emails

    # Sending email
    def send_email(self, message, isException):
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = ", ".join(self.exception_recipient_emails) if isException else ", ".join(self.recipient_emails)
        msg['Subject'] = "Visa Availability Notification"
        msg.attach(MIMEText(message, 'plain'))

        try:
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            if isException:
                server.sendmail(self.email_user, self.exception_recipient_emails, text)
            else:
                server.sendmail(self.email_user, self.recipient_emails, text)
            server.quit()
        except Exception as e:
            print(f"An error occurred while sending email: {e}")
            self.logger.error(f"An error occurred while sending email: {e}")


class RedisSvc:
    # Initialize RedisReceiver
    def __init__(self, host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        try:
            self.r = redis.Redis(host=host, port=port, db=db)
            self.r.ping()
        except redis.ConnectionError as e:
            print("Cannot connect to Redis server. Please make sure the server is running and the host and port are correct.")
            self.logger.error(f"An error occurred: {e}")

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
                    #print(f"Received message: {message_data}")
                    return message_data
                else:
                    time.sleep(1)
        except redis.RedisError as e:
            print(f"An error occurred when receiving a message: {e}")
            self.logger.error(f"An error occurred when receiving a message: {e}")
            raise


if __name__ == "__main__":
    # Initialize global variables
    filePath = FILE_PATH
    fileNamePrefix = FILE_NAME_PREFIX
    fileSuffix = date.today().strftime("%Y-%m-%d")

    #Delete old files
    fileLocal = FileLocal(filePath, fileNamePrefix)
    fileLocal.clean_old_files(days=DELETE_FILE_IN_DAYS)

    # Configure the logger
    logging.basicConfig(filename=rf'{filePath}\{fileNamePrefix}-log-{fileSuffix}.log',
                        level=logging.DEBUG,
                        format='%(asctime)s %(message)s')

    #API config
    url = API_URL
    headers = {
        'Cookie': '',
        'User-Agent': USER_AGENT
    }
    service_id = SERVICE_ID
    num_months = NUM_MONTHS_TO_FETCH

    # Email configuration
    email_server = EMAIL_SERVER  # SMTP server
    email_port = EMAIL_PORT  # SMTP port
    email_user = EMAIL_USER  # Your email address "zhhlbaw2011@outlook.com"  ""zhhlbaw2016@outlook.com""
    email_password = EMAIL_PASSWORD  # Your email password
    recipient_emails = RECIPIENTS  # Recipient email address ["zhhlbaw2011@gmail.com", "hzhou55@asu.edu"]
    exception_recipient_emails = EXCEPTION_RECIPIENTS

    #Initialize VisaAvailability class
    visaAvailability = VisaAvailability(url, headers, service_id, num_months, filePath, fileNamePrefix, fileSuffix, email_server, email_port, email_user, email_password, recipient_emails, exception_recipient_emails)
    params = visaAvailability.get_parameters()

    # Schedule the get_availability method to be called every {API_SCHEDULE} minute
    #schedule.every(1).minutes.do(visaAvailability.get_availability)
    schedule.every(API_SCHEDULE).minutes.do(lambda: visaAvailability.get_availability(params))

    while True:
        schedule.run_pending()
        time.sleep(1)
