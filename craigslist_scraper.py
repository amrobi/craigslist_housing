# -*- coding: utf-8 -*-
"""
@author: lmcox
"""
#%%
#import get to call a get request on the site
import requests
from bs4 import BeautifulSoup
from datetime import date
import time
import os

#%%
def get_html_from_pages(number_of_pages, filepath=None, sleep_time=30):
    current_page = 360
    current_date = str(date.today())
    timestamp = str(time.time())
    save_file_text = 'The ' + str(number_of_pages) + 'pages of posts in this directory were downloaded on ' + current_date + ' at ' + timestamp
    if filepath != None:
        savefile = os.path.join(filepath, '__date_saved.txt')
    else: savefile = '__date_saved.txt'
    with open(savefile, 'w') as f:
        f.write(save_file_text)
    while (current_page/120) <= number_of_pages:
        print("No longer sleeping")
        page_url = 'https://chicago.craigslist.org/d/apartments-housing-for-rent/search/apa?s=' + str(current_page)
        one_page = requests.get(page_url)
        html_soup = BeautifulSoup(one_page.text, 'html.parser')
        posts = html_soup.find_all('li', class_= 'result-row')

        for one_post in posts:
            post_one_title = one_post.find('a', class_='result-title hdrlnk')
            post_one_id = post_one_title['id']
            url = post_one_title['href']
            filename = str(post_one_id) + '.txt'
            if filepath != None:
                filename = os.path.join(filepath, filename)
            print(filename, url)
            raw_html=requests.get(url)
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(raw_html.text)
        current_page += 120
        print("Sleeping now")
        time.sleep(sleep_time)

if __name__ == '__main__':
    get_html_from_pages(20, 'html', sleep_time=5)
