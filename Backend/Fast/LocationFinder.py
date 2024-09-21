from playwright.async_api import async_playwright, expect
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pandas as pd
import requests
from datetime import datetime
import time
# from PW_PropertyDetail import *
import re
import requests
import urllib.request
import json

async def getPlaceID(locationname):
    placeID = ""
    print("================================================================")
    print(locationname)
    url = "https://www.bigbasket.com/places/v1/places/autocomplete?inputText=" + \
        locationname.replace(" ","%20")+"&token=6a390ccb-873c-494-8000-362bb96ee123"
    print(url)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
        content = json.loads(the_page)
        print(type(content))
        placeID = content['predictions'][0]['placeId']
    #return placeID
    return await getLatLong(placeID)

async def getLatLong(placeID):
    print(placeID)
    foundLocationName = ""
    latlong = []
    print("================================================================") 
    url = "https://www.bigbasket.com/places/v1/places/details/?placeId=" + \
        placeID+"&token=6a390ccb-873c-494-8000-362bb96ee123"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        the_page = response.read()
        content = json.loads(the_page)
        print(type(content))
        foundLocationName = content['geometry']
        latlong.append(str(foundLocationName['location']['lat']))
        latlong.append(str(foundLocationName['location']['lng'])) 
    print("latlong******")
    print(type(latlong))
    print(latlong)
    return latlong
        
async def load(url):
    url = url.replace(' ', '+')
    print(url)
    print(datetime.now())
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url)

        # Wait for the URL to contain '@'
        await page.wait_for_function('window.location.href.includes("data")')

        # Optionally, verify the URL or perform additional actions
        latlong = page.url.split('@')
        current_url = latlong
        return str(current_url[1]).split(',')[0:2]

# readURL()

if __name__ == '__main__':
    import asyncio
    asyncio.run(load())
    # value = ["mg road"]
    # print(len(value))
    # readURL()
