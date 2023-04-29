import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from bs4 import BeautifulSoup, SoupStrainer
import re
import random

import datetime
import time
from time import strftime

import pymongo
import sys

import urllib.parse

timeout_sec = 8

CONNECTION_STRING = "mongodb+srv://br4pk33t:MJITz7Jc6o5LzwN2@cluster0.fdzzwnj.mongodb.net/?retryWrites=true&w=majority"

#save local
f = open("amaz_res.txt","w", encoding="utf-8")


try:
  client = pymongo.MongoClient(CONNECTION_STRING)

except pymongo.errors.ConfigurationError:
  print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
  sys.exit(1)

db = client.amazdb
my_collection = db["amazcol"]

product_links = []

for product in my_collection.find():
  if not product in product_links:
    product_links += [product["link"]]    


print("starting scraping ....")

for current_page in range(1,50):

    try:
        print("\ncurrent page: " + str(current_page))
        url = "https://www.amazon.com/s?k=Electronics+Accessories+%26+Supplies&i=electronics-accessories&page="+ str(current_page)
        print("current url: " + str(url))


        software_names = [SoftwareName.CHROME.value]
        operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
        user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
        # Get list of user agents.
        user_agents = user_agent_rotator.get_user_agents()
        # Get Random User Agent String.
        user_agent = user_agent_rotator.get_random_user_agent()
        print("user_agent")
        print(user_agent)



        # headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'}
        headers = {
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': user_agent,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.amazon.com/',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        response = requests.get(url, headers=headers)
        res_text = response.text
        soup = BeautifulSoup(res_text, 'html.parser')
        site_arr = []





        for i in soup.find_all('div',attrs={'class':'a-section a-spacing-small a-spacing-top-small'}):

            current_article = {
                "name" : "",
                "desc" : "",
                "rating" : "",
                "price" : [],
                "link" : "",
                "time" : ""
            }

            now = datetime.datetime.now()
            current_article["time"] = str(now)


            for i2 in i.find_all('span',attrs={'class':'a-size-medium a-color-base a-text-normal'}):
                current_article["name"] = i2.text


            price_str = ""

            for i3 in i.find_all('span',attrs={'class':'a-price-whole'}):
                price_str += i3.text

            for i4 in i.find_all('span',attrs={'class':'a-price-fraction'}):
                price_str += i4.text




            for i5 in i.find_all('span',attrs={'class':'a-icon-alt'}):
                rating = i5.text.split(" ")[0]
                current_article["rating"] = rating


            for i6 in i.find_all('a',attrs={'class':'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'}):
                link = i6['href']
                link_split = ""

                if not re.search('url=.*ref%3D', link) == None:
                    z = re.search('url=.*ref%3D', link).group(0)
                    link_split = z.replace("url=","")
                    link_split = link_split.replace("%2Fref%3D","")
                    link_split = link_split.replace("%2F","/")
                else:
                    link_split = link.split('/ref=')[0]

                current_article["link"] = link_split






            price_obj = {
                "price" : "",
                "date" : ""
            }

            #float throws err if no price available
            #try err so only kills current loop
            try:
                price_obj["price"] = float(price_str)
                price_obj["date"] = str(now)
                print("Is float")
            except Exception as err_float:
                print("Not a float")
                print(err_float)

            print("price_obj")
            print(price_obj)


            if not current_article["name"] == "" and not current_article["rating"] == "" and not price_obj["price"] == "" and not current_article["link"] == "" and not current_article["link"] in product_links:                   
                
                #decoding
                current_article["link"] = urllib.parse.unquote(current_article["link"])

                current_article["price"] = [price_obj]
                print("current_article")
                print(current_article)
                site_arr += [current_article]
                product_links += [current_article["link"]]


        print("finish ... printing array ....")

        for article in site_arr:
            # local
            # print(article)
            f.write(article["link"] + '\n')
            f.flush()

        print("writing to db....")

        try: 
            result = my_collection.insert_many(site_arr)

        except pymongo.errors.OperationFailure:
            print("An authentication error was received. Are you sure your database user is authorized to perform write operations?")
            sys.exit(1)
        else:
            inserted_count = len(result.inserted_ids)
            print("I inserted %x documents." %(inserted_count))
            print("saved to mongodb!")
        
    except Exception as err_loop:
        print('[ERR] loop error')
        print(err_loop)
        
    random_sleep_sec = random.randint(3, timeout_sec)
    print("sleeping " + str(random_sleep_sec) + " sec then going to next ....")    
    time.sleep(random_sleep_sec)
        
print('***END')