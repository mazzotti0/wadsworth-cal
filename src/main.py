import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from scraper import WadsworthScraper
import datetime
import pandas as pd
import logging
import time
from configparser import ConfigParser



def month_range(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        yield current_date.strftime("%B %Y")
        current_month = current_date.month
        current_year = current_date.year
        if current_month == 12:
            current_month = 1
            current_year += 1
        else:
            current_month += 1
        current_date = datetime.datetime(current_year, current_month, 1)

def generate_month_list(start_date, end_date):
    start_date = datetime.datetime.strptime(start_date, '%Y-%m')
    end_date = datetime.datetime.strptime(end_date, '%Y-%m')
    return list(month_range(start_date, end_date))


def check_for_availability(df, start_date, end_date): 
    
    availabilities_df = df[(df['date_saturday'] <= end_date) & 
                            (df['date_saturday'] >= start_date) & 
                            (df['event_count'] == 0)]

    if availabilities_df.shape[0] > 0:
        date_list = []
        for i, row in availabilities_df.iterrows(): 
            date_list.append(str(row['date_saturday'].date()))

        message = f"The following dates have become available: {(', '.join(str(v) for v in date_list).strip(','))}"

        return message
    else:
        return 

def send_email(df, alert_message, sender, password): 
    # email details
    sender_email = sender
    receiver_email = sender
    password = password

    # create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = f"Wadsworth 2024 Saturday Alert: {str(datetime.datetime.now())}"
    body = df.to_string()
    message.attach(MIMEText(alert_message + "\n", "plain"))
    message.attach(MIMEText(body, "plain"))

    # send email
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(sender_email, password)
        smtp.sendmail(sender_email, receiver_email, message.as_string())
    


if __name__ == '__main__': 
    
########################
###  SET UP LOGGING  ###
########################
    
    # configure logging
    logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info('Logging configured for session')
    
########################
###    RUN SCRIPT    ###
########################
    
    # read in secrets
    parser = ConfigParser()
    _ = parser.read('../credentials.cfg')
    sender = parser.get('my_email','my_username')
    password = parser.get('my_email','my_password')
    
    # set variables
    begin_time = time.perf_counter()
    scraper = WadsworthScraper()
    results_df = pd.DataFrame()
    start_date = '2024-05-01'
    end_date = '2024-10-31'

    logging.info('getting Wadsworth 2024 calendar information...')
    for month in generate_month_list('2024-01','2024-12'):
        
        month_dt = datetime.datetime.strptime(month, '%B %Y')
        data = scraper.get_and_parse_month(month_dt.year, month_dt.month)
        month_df = pd.json_normalize(data)
        month_df['month'] = month
        
        results_df = pd.concat([results_df, month_df[['month','date_saturday','event_count']]])
        results_df['date_saturday'] = pd.to_datetime(results_df['date_saturday'])
        results_df['event_count'] = results_df['event_count'].astype(int)
    
    logging.info(f'checking for availability between {start_date} and {end_date}...')
    alert_message = check_for_availability(results_df, start_date, end_date)
    
    if alert_message:
        logging.info('NEW AVAILABILITIES FOUND!')
        send_email(results_df, alert_message, sender, password)
    else: 
        logging.info('no availabilities found between specified dates')
    
    end_time = time.perf_counter()
    total_time = end_time - begin_time 
    logging.info(f'script completed in {total_time:0.6f} seconds')
    
