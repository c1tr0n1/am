import requests
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

import numpy as np

from concurrent.futures.thread import ThreadPoolExecutor

from bs4 import BeautifulSoup, SoupStrainer
import re
import random

import datetime
import time
from time import strftime

import pymongo
import sys

#todo:
#change proxy if err

#save log
f = open("amaz_log.txt","w", encoding="utf-8")

CONNECTION_STRING = "mongodb+srv://br4pk33t:MJITz7Jc6o5LzwN2@cluster0.fdzzwnj.mongodb.net/?retryWrites=true&w=majority"

username = "fwqoopaf"
pw = "qfi172f2z1d2"

w_proxies = [
    '185.199.228.220:7300',
    '185.199.231.45:8382',
    '188.74.210.207:6286',
    '188.74.183.10:8279',
    '188.74.210.21:6100',
    '45.155.68.129:8133',
    '154.95.36.199:6893',
    '45.94.47.66:8110',    
    '2.56.119.93:5074',
    '185.199.229.156:7492'
]

try:
  client = pymongo.MongoClient(CONNECTION_STRING)

except pymongo.errors.ConfigurationError:
  print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
  f.write("mongodb err\n")
  sys.exit(1)

db = client.amazdb
my_collection = db["amazcol"]

product_links = []

for product in my_collection.find():
  if not product in product_links:
    product_links += [product["link"]]    


def get_auth_proxy(proxy):
    res_proxy = {
        "http": "http://" + str(username) + ":" + str(pw) + "@" + str(proxy)
    }
    return res_proxy

def get_rnd_header():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()

    header = {
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

    return header

def get_amaz_price_proxy(req_url,proxy):

    price_obj = {
        "price" : "",
        "date" : ""
    }
   
    try:
        #checking proxy
        cur_proxy = get_auth_proxy(proxy)        
        url = "https://www.showmyip.com"
        response = requests.get(url, proxies=cur_proxy)
        res_text = response.text

        soup = BeautifulSoup(res_text, 'html.parser')

        for i in soup.find_all('h2',attrs={'id':'ipv4'}):
            print('proxy connected!')
            print(i.text)


        #get amaz
        url = "https://www.amazon.com" + str(req_url)
        header = get_rnd_header()      

        response = requests.get(url, headers=header,proxies=cur_proxy)
        res_text = response.text
        soup = BeautifulSoup(res_text, 'html.parser')

        for i in soup.find('span',attrs={'class':'a-price'}):
            price_str = ""

            for i3 in i.find_all('span',attrs={'class':'a-price-whole'}):
                price_str += i3.text

            for i4 in i.find_all('span',attrs={'class':'a-price-fraction'}):
                price_str += i4.text

            now = datetime.datetime.now()
            try:                
                price_obj["date"] = str(now)
                price_obj["price"] = float(price_str)
            except Exception as err_float: #float fail
                print("err_float")
                print(err_float)

        if price_obj["price"] == "":            
            try:
                for i_span in soup.find_all('span',attrs={'class':'a-price a-text-price a-size-medium apexPriceToPay'}):
                    print("i_span")
                    print(i_span)
                    #to fix
                    for i_span_price_ele in i_span.find_all('span',attrs={'class':'a-offscreen'}):                        
                        i_span_price_ele_res_price = i_span_price_ele.text
                        i_span_price_ele_res_price = i_span_price_ele_res_price.replace("$","")
                        now = datetime.datetime.now()
                        try:             
                            price_obj["date"] = str(now)   
                            price_obj["price"] = float(i_span_price_ele_res_price)
                        except Exception as err_float_float: #float fail
                            print("err_float_float")
                            print(err_float_float)
                            price_obj["date"] = str(now)   
                            price_obj["price"] = float(1)

            except Exception as err_float2:
                print("Not a float err_float2")
                print(err_float2)


            print("price_obj")
            print(price_obj)

    except Exception as  err_gapp:
        print('[ERR] in get_amaz_price_proxy()')
        print(err_gapp)


    return price_obj

def mongodb_update_price(product_url,new_price_obj):    
    res_obj = {
        'matched' : '',
        'modified' : ''
    }
    print('\nupdating entry ...')
    try:          
        to_update = {
            "price" : new_price_obj
        }        

        find_article = my_collection.update_one({"link": product_url},{"$push":to_update})        
        res_obj['matched'] = find_article.matched_count        
        res_obj['modified'] = find_article.modified_count

    except pymongo.errors.OperationFailure:
        print("[ERR] mongodb_update_price()")
        # sys.exit(1)
    else:
        print("inserted new arr mongodb")

    return res_obj

def run_price_update(product_links,product_links_i):

    proxy = w_proxies[product_links_i]
    print('\n\nSTARTING ARRAY')
    print('running run_price_update with: ')
    print('product_links: ' + str(product_links))
    print('proxy        : ' + str(proxy))

    try:
        for product_link in product_links:
            print('\n')
            print('array       : ' + str(product_links_i))
            print('proxy       : ' + str(proxy))
            print('product_link: ' + str(product_link))
            f.write(str(product_links_i) + '\n')
            f.write(str(proxy) + '\n')
            f.write(str(product_link) + '\n')

            price_object = get_amaz_price_proxy(product_link,proxy)

            print('retrieved price_object:')
            print(price_object)
            f.write(str(price_object) + '\n')

            res_update = mongodb_update_price(product_link,price_object)
            print("res_update")
            print(res_update)
            f.write(str(res_update) + '\n')

            random_sleep_sec = random.randint(2, 7)
            print("sleeping " + str(random_sleep_sec) + " sec then going to next ....")    
            time.sleep(random_sleep_sec)
            f.write('\n\n')


    except Exception as err_run_price_update:
        print('[ERR] run_price_update()')
        print(err_run_price_update)
        f.write(str(err_run_price_update) + '\n')


def start_check_proxies_threads():
    print('trying to update ' + str(len(product_links)) + ' products...')
    
    product_links_arrs = np.array_split(product_links, len(w_proxies)-2)
    with ThreadPoolExecutor(max_workers=len(product_links_arrs)) as executor:
        proxy_i = 0
        for proxy_link_arr in product_links_arrs:
            print('starting to check ' + str(proxy_i) + "array (" + str(len(proxy_link_arr)) + ")")
            executor.submit(run_price_update, proxy_link_arr, proxy_i)
            proxy_i += 1

    print('******updated')


while True:
    ts = time.time()
    rest = int(ts) % 600
    print(str(rest))
    if rest == 0:
        start_check_proxies_threads()
    time.sleep(1)

