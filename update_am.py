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


#save log
f = open("amaz_log.txt","w", encoding="utf-8")

fl_arr = []

CONNECTION_STRING = "mongodb+srv://br4pk33t:MJITz7Jc6o5LzwN2@cluster0.fdzzwnj.mongodb.net/?retryWrites=true&w=majority"

try:
  client = pymongo.MongoClient(CONNECTION_STRING)

except pymongo.errors.ConfigurationError:
  print("An Invalid URI host error was received. Is your Atlas host name correct in your connection string?")
  f.write("mongodb err\n")
  sys.exit(1)


prox_db = client.proxdb
prox_collection = prox_db["proxcol"]
all_proxies = []
for prox in prox_collection.find():
    if not prox in all_proxies:
        all_proxies += [prox]    


links_db = client.amazdb
links_collection = links_db["amazcol"]
all_links = []
for p_link in links_collection.find():
  if not p_link in all_links:
    all_links += [p_link["link"]]    


def get_rnd_header():
    software_names = [SoftwareName.CHROME.value]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
    user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=100)
    user_agent = user_agent_rotator.get_random_user_agent()

    header = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
    }

    return header


def get_price(req_url,p):

    print('\n################################################')
    print('trying to get price ..... ')
    print('req_url: ' + str(req_url))
    print('p      : ' + str(p))
    print('################################################')

    rnd_header = get_rnd_header()

    price_obj = {
        "price" : "",
        "date" : "",
        "header" : rnd_header
    }
   
    try:
        #get amaz
        amaz_url = "https://www.amazon.com" + str(req_url)

        amaz_response = requests.get(amaz_url, headers=rnd_header, proxies=p["proxy"])
        amaz_res_text = amaz_response.text
        soup = BeautifulSoup(amaz_res_text, 'html.parser')

        for i in soup.find('span',attrs={'class':'a-price'}):
            price_str = ""
            for i3 in i.find_all('span',attrs={'class':'a-price-whole'}):
                price_str += i3.text
            for i4 in i.find_all('span',attrs={'class':'a-price-fraction'}):
                price_str += i4.text
            now = datetime.datetime.now()
            now = now + datetime.timedelta(hours=+2)
            try:            
                price_obj["date"] = str(now)
                price_obj["price"] = float(price_str)
            except Exception as err_float: #float fail
                print("err_float")
                print(err_float)


        if price_obj["price"] == "" or not isinstance(price_obj["price"], float):  

            try:
                for i_span in soup.find_all('span',attrs={'class':'a-price'}):
                    for i_span_price_ele in i_span.find_all('span',attrs={'class':'a-offscreen'}):                        
                        i_span_price_ele_res_price = i_span_price_ele.text
                        i_span_price_ele_res_price = i_span_price_ele_res_price.replace("$","")
                        i_span_price_ele_res_price = i_span_price_ele_res_price.replace(",",".")
                        now = datetime.datetime.now()
                        now = now + datetime.timedelta(hours=+2)
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

    except Exception as  err_gapp:
        print('[ERR] in get_amaz_price_proxy()')
        print(err_gapp)

    return price_obj


def mongodb_update_price(product_url,new_price_obj):    
    res_obj = {
        'matched' : '',
        'modified' : ''
    }
    try:          
        to_update = {
            "price" : new_price_obj
        }        

        find_article = links_collection.update_one({"link": product_url},{"$push":to_update})        
        res_obj['matched'] = find_article.matched_count        
        res_obj['modified'] = find_article.modified_count

    except pymongo.errors.OperationFailure:
        print("[ERR] mongodb_update_price()")
    else:
        print("inserted new arr mongodb")

    return res_obj


def run_update(product_links_arr,product_links_i,proxy):

    global fl_arr

    try:
        for product_link in product_links_arr:

            fl_obj = {
                'url' : str(product_link),                 
                'proxy' : str(proxy['proxy']),
                "header" : ""               
            }
                        
            try:
                print('\n')
                print('array       : ' + str(product_links_i))
                print('url         : ' + str(product_link))
                print('proxy       : ' + str(proxy["proxy"]))
                
                f.write('array  : \n' + str(product_links_i) + '\n')
                f.write('url    : \n' + str(product_link) + '\n')
                f.write('proxy  : \n' + str(proxy["proxy"]) + '\n')
                f.write('\n')


                curr_price = get_price(product_link,proxy)
                fl_obj['header'] = curr_price['header']

                print("curr_price")
                print(curr_price)

                if curr_price["price"] == '':
                    fl_arr += [fl_obj]

                else:                    
                    f.write(str(curr_price) + '\n')            
                    mongodb_update_price_res = mongodb_update_price(product_link,curr_price)

                    if mongodb_update_price_res["matched"] != 1 or mongodb_update_price_res["modified"] != 1:
                        fl_arr += [fl_obj]
                    else:
                        f.write(str(mongodb_update_price_res) + '\n')
                        print('******updated')
                        
            except Exception as product_link_exception:
                print('[ERR] for ... try ... exception')
                print(product_link_exception)
                fl_arr += [fl_obj]

            f.write('\n\n')


    except Exception as err_run_price_update:
        print('[ERR] err_run_price_update()')
        print(err_run_price_update)
        fl_arr += [fl_obj]


def update_fl_arr(fl_array):
    bk_prox_int = 5
    try:
        for fl_link in fl_array:
            curr_price = get_price(fl_link,all_proxies[bk_prox_int])
            while curr_price["price"] == "" and bk_prox_int < len(bk_prox_int):
                bk_prox_int = bk_prox_int + 1
                curr_price = get_price(fl_link,all_proxies[bk_prox_int])
            if not curr_price["price"] == "":
                mongodb_update_price_res = mongodb_update_price(fl_link,curr_price)
            else:
                final_f_arr += [fl_link]

    except Exception as fl_err:
        print("fl_err")
        print(fl_err)
        final_f_arr += [fl_link]


def start_updating():    
    product_links_arrs = np.array_split(all_links, len(all_proxies)/2)
    with ThreadPoolExecutor(max_workers=len(product_links_arrs)) as executor:
        proxy_i = 0
        for proxy_link_arr in product_links_arrs:
            executor.submit(run_update, proxy_link_arr, proxy_i, all_proxies[proxy_i])
            proxy_i += 1

        # update_fl_arr(fl_arr)

while True:
    ts = time.time()
    rest = int(ts) % 600
    print(str(rest))
    if rest == 0:
        start_updating()
    time.sleep(1)



