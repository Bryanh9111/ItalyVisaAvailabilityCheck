import requests, os, time, json
import os
import glob
import platform
from datetime import datetime, timedelta
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

# The directory where the files are located
path = r"C:\Users\zhhlb\OneDrive\桌面"

# Two days ago from now
two_days_ago = datetime.now() - timedelta(days=2)

# Use glob to find all txt files in the directory that start with "visaDates"
for file_name in glob.glob(os.path.join(path, "visaDates*.txt")):
    # Get the creation date of the file
    file_date = datetime.fromtimestamp(creation_date(file_name))
    # If the file was created on or before two days ago, delete it
    if file_date.date() <= two_days_ago.date():
        os.remove(file_name)



with open(rf'C:\Users\zhhlb\OneDrive\桌面\visaDates-{date.today().strftime("%Y-%m-%d")}.txt', 'a', encoding='utf8') as f:
    f.write(f"{'-'*30}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{'-'*30}" + '\n')

# https://prenotami.esteri.it/Services/RetrieveServices （here we can get cookie） GET, we can get service_id here as a list, 2354 is shenggen
# https://prenotami.esteri.it/Services/GetBookingTypes GET
# https://prenotami.esteri.it/BookingCalendar
# https://prenotami.esteri.it/BookingCalendar/RetrieveServerInfo
url = 'https://prenotami.esteri.it/BookingCalendar/RetrieveCalendarAvailability'
headers = {
    'Cookie': '_Culture=1; BIGipServerpool_prenotami.esteri.it=rd21o00000000000000000000ffffc0a806e8o443; _pk_ses.E1e0Ge2p6l.5f67=1; _pk_id.E1e0Ge2p6l.5f67=9c9c42707d323fe8.1687214245.1.1687214506.1687214245.; .cookie.=j8-fZznvqoKS1GYdmGzV67HuxRQp6awqy6hLQOv6o2MrsOM11U8xjnzqeD_b-9VeXmJYZeldk6MFfstjRuCRQYSbXQdMyQS_NK83Xs3EsAmH2GmArD0Rz9tDBIQ1GU7phknCTjW9D84nf2TDBtb7870ohQ5dosvPgZGkDaSmbAwHHaJGoQ4SHBkD3LvZiE6Ihrnjmig7zFn7sC90Isfbw1M0ZDA2Dk9bkw5VklNIZLbbqAr4UFlG-zwrNwPye7H9Llbtas3uVAe1yWU0HFiMbJGV0KLJUOeY69LNcOMOpSL5V3r-wWgaGTgSnPTjLcStG33cyqZNWsHqvc-mqkZtL0eNujbz0S4eshQVh4DdzkaD40_NObBLUcxwCPgfJOffqz0nb8q_hX0-TVHjLYVDQYkqJMF4knuwDJkZHoAjVhsuBYvkK611sr1VRAWOtbjtgOb-g7H497a1KsA812aF9mORprU1KeMiAMfuPiEHOAOzyngJyaihd8Qh0XwZWZ5Y2zTXWpdU6I7l_kKPtYPD1H7BqAALdcKBhRIEBf65MEFOkL3mjNkCneHz5K618d63drjeTmkWTZiJyugp7_0ppsrJ5STanYUsCCYT8sgwkBo; TS01412fac030=01574ed751e537ae3a41a8747961861d53c5bfa4b9cee5454668a0f83293e6ad25c4056ec36498087c9bba19348e455724aa3f4825; OClmoOot=A4D1zdWIAQAATMBwf6eKt4mJNesjR4fJM0r8Rw74eB9fMxneeFZ92yXTtU7IAY5-sW6uchRAwH8AAEB3AAAAAA|1|1|c7a244309a60f60ce4ca7486a51ab552114660eb; ASP.NET_SessionId=tz40rzehy2tp2obrngtmu5wk; Lyp1CWKh=Axmuz9WIAQAAdS5w4oMXaK705-AXplL8uBiEEgbbrVZhTOAWUY_ObUqKc6tqAY5-sW6uchRAwH8AAEB3AAAAAA==; TS01412fac=01a6f07363f8943c1c0f5aeb9b785869e86bbbb8fc289199acadda29f2c01a744db3232a5b3ae1d70dbdc813eab5e1ef88f1bcef9d9175ff613c9b729bdf0683e27866896cad115ae0c7d268115ec70caa5b689b1235f38852009a0791d5af4e1431432c7cd03d6531441ea5199858e951ace93aac36f693f6b1b53003288d474b12b5f6c80a766d097fe0bf6c9f874649932d6ede',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
}

# Get today's date
today = datetime.today()

# Define the start date as the first day of the current month
start_date = datetime(today.year, today.month, 1)

# Define the number of months to generate
num_months = 4

# Define the service ID
service_id = '2354'#'840'#'2354'

# Initialize an empty list to store the parameter objects
params = []

# Generate the list of parameter objects
for month_offset in range(num_months):
    # Calculate the first day of the current month
    current_date = start_date + relativedelta(months=month_offset)
    current_date_str = current_date.strftime('%Y-%m-01')

    # Create the parameter object
    param = {
        'selectedDay': current_date_str,
        '_Servizio': service_id
    }

    # Add the parameter object to the list
    params.append(param)

# Print the generated list
for param in params:
    date_string = param["selectedDay"]
    date_object = datetime.strptime(date_string, "%Y-%m-%d")
    year = date_object.year
    month = date_object.month
    print(year, month)
    # Get Json results from POST API Call
    print('Parm:' + param['selectedDay'])
    result = requests.post(url, params=param, headers=headers).text
    resultJson = json.loads(result)
    # result = requests.post(url, params=params, headers=headers)
    # resultJson = result.json()
    # print(resultJson)

    dic_resultJson = json.loads(resultJson)
    print(f'{len(dic_resultJson)} dates on the portal') #print('{} dates on the portal'.format(len(resultJson)))
    for entry in dic_resultJson:
        # if entry["SlotLiberi"] == 0:
        date_string = entry['DateLibere']
        date = datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S")
        formatted_date = date.strftime("%Y-%m-%d")
        print(f"There are {entry['SlotLiberi']} slots on {formatted_date}")
        with open(rf'C:\Users\zhhlb\OneDrive\桌面\visaDates-{date.today().strftime("%Y-%m-%d")}.txt', 'a', encoding='utf8') as f:
            f.write(f"There are {entry['SlotLiberi']} slots on {formatted_date}" + '\n')






















































