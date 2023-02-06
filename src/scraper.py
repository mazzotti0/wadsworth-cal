import requests
from bs4 import BeautifulSoup
import re
import datetime
import pandas as pd
from configparser import ConfigParser


class WadsworthScraper:
    
    parser = ConfigParser()
    _ = parser.read('../credentials.cfg')
    browser = parser.get('my_browser','user_agent')
    
    # function to get a month of calendar data
    def get_calendar_month(self, year, month):
        API_url = 'https://www.wadsworthmansion.com/wp-admin/admin-ajax.php'
        headers = {'User-Agent':self.browser,
                  "X-Requested-With": "XMLHttpRequest"}
        payload = {
                    "action": "simcal_default_calendar_draw_grid",
                    "month": month,
                    "year": year,
                    "id": 28897
                }

        # Making the post request
        response = requests.post(API_url, 
                                 headers=headers, 
                                 data=payload)
        # get the data
        if response.status_code == 200: 
            data = response.json()['data']
            return data

        else: 
            print('error making request: ', response.status_code)
            print(response.json())
    
    # parse a month of data to get wedding dates
    def parse_month(self, data, year, month):
    
        saturdays_list = []

        #set up for parsing
        soup = BeautifulSoup(data, "html.parser")

        #get each week row in the month object
        weeks = soup.find_all('tr', 'simcal-week')

        #loop through weeks and only get valid days (exclude void days)
        for week in weeks: 
            days = week.find_all('td', re.compile('simcal-day-\d.*'))

            # loop through valid days to get events data - limit to saturdays
            for day in days:
                day_attrs = day.attrs['class']
                if day_attrs[1] == 'simcal-weekday-6': 
                    calendar_day = datetime.datetime(year, month, int(day_attrs[0].split('-')[-1]))
                    event_count = day.attrs['data-events-count']
                    saturdays_list.append({
                        'date_saturday':calendar_day.date(),
                        'event_count':event_count
                        }
                    )

        return saturdays_list
    
    def get_and_parse_month(self, year, month):
        data = self.get_calendar_month(year, month)
        month_data = self.parse_month(data, year, month)
        return month_data

