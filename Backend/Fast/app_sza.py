import sqlite3
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import asyncio
from LocationFinder import *
import json
import os
from bs4 import BeautifulSoup

app = FastAPI()
db_path = os.path.join('..', 'DB', 'SZA.db')


class Item(BaseModel):
    lat: float
    long: float
    radius: float


class NLPQuery(BaseModel):
    query: str


@app.post("/filter")
async def filter(item: Item):
    print(":Reached here:")
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row

    # Query to filter data
    print(type(item))
    print(item)
    lat = float(item.lat)
    long = float(item.long)
    radius = float(item.radius)

    print(lat)
    # Prepare the query using parameterized inputs

    # Prepare the query using parameterized inputs
    query = """
            SELECT * FROM tb_properties
            WHERE (
                6371 * ACOS(
                    COS(RADIANS(90 - latitude)) * COS(RADIANS(90 - :input_lat)) +
                    SIN(RADIANS(90 - latitude)) * SIN(RADIANS(90 - :input_lat)) *
                    COS(RADIANS(longitude - :input_long))
                )
            ) <= :radius;
            """

    # Print the parameters being used
    print(90 - lat, 90 - lat, long, radius)

    # Execute the query with named parameters
    params = {
        'input_lat': lat,
        'input_long': long,
        'radius': radius
    }

    cursor.execute(query, params)

    # Fetch and print results
    rows = cursor.fetchall()
    print(rows)
    colnames = cursor.description
    columns = list()
    for row in colnames:
        columns.append(str(row[0]))
    print(columns)

    # Convert each row to a list of values
    row_values = [list(row) for row in rows]
    print(row_values)

    results = []
    for row in row_values:
        results.append(dict(zip(columns, row)))
    print(results)
    # Close the connection
    cursor.close()
    conn.close()
    return results


@app.get('/getPropertyDetails/{property_id}')
async def getPropertyDetails(property_id: str): 
    #https://www.stanzaliving.com/_next/data/1724744444870/bengaluru/pg-hostel-near-reva-university/male/incheon-house.json
    print(property_id.replace('%2', '/'))
    property_id = property_id.replace('%2', '/') 
    #url = 'https://www.stanzaliving.com/_next/data/1724744444870/'+property_id+".json"
    url = 'https://www.stanzaliving.com/'+property_id
    print(url)   
    x = requests.get(url)
    # final_answer = x.text
    # Check if the request was successful
    if x.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(x.text, 'html.parser')
        
        # Find the script tag with the specified id
        script_tag = soup.find("script", id="__NEXT_DATA__")
        
        if script_tag:
            # Get the text content inside the script tag
            script_content = script_tag.string
            # Parse the JSON content
            try:
                json_data = json.loads(script_content)
                return json_data['props']  # Now you can work with the JSON object
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
        else:
            print("Script tag with id '__NEXT_DATA__' not found.")
    else:
        print(f"Failed to retrieve the page: {x.status_code}")
        #print(final_answer)
   # extract_metadata(final_answer)
    #return final_answer

@app.post('/find')
async def find(query: NLPQuery):
    query = query.query 
    print(db_path)
    print(query)
    url = 'http://localhost:11434/api/generate'
    myobj = {"model": "llama3", "stream": False, "prompt": "''' You have to summarized answer "
             "In the following query extract the location name"
                                                           " and pincode and longitude and latitude and radius and minimum and maximum budget."
                                                           "If able to convert the extracted location name into latitude and longitude do it other wise dont convert."
                                                           "if you not sure say "". return the value with the only dictionary format location_name, longitude, latitude pincode, min_price, max_price,radius. radius expecting as float in killometer unit. Output should be a dictionary format, Should not contain any other string."""
                                                           "'Query:'. Show only answer and dont add the query in the "
                                                           "answer. Dont add Here is the summarized answer:"
                                                           "block.\n\nQuery:" + query + ".'''"}
    print(myobj)
    x = requests.post(url, json=myobj)

    final_answer = x.json()

    print((eval(final_answer['response'])['location_name']))
    location_name = (eval(final_answer['response'])['location_name'])
    radius = (eval(final_answer['response'])['radius'])
    print(location_name)
    # print(a)
    # latlong = await load("https://www.google.com/maps/place/"+location_name+" ,Bengaluru")
    latlong = await getPlaceID(location_name)
    print(latlong)
    if len(latlong) > 1:
        # return {"lat":lat,"long":long,"radius":radius}
        url = 'http://127.0.0.1:8002/filter'
        print("latitid")
        myobj = {"lat": latlong[0], "long": latlong[1], "radius": radius}
        # myobj = json.dumps(myobj)
        print(myobj)
        # x = await requests.post(url, json=myobj)
        # final_answer = x.json()
        item = Item(**myobj)
        filter_results = await filter(item)
        return filter_results
    else:
        return {location_name + " is not able identify, Please check the location."}

    return "Exit"


def extract_metadata(property_json): 
    
    propertyname_path = property_json['pageProps']['residenceDetails']['name']
    description_path = property_json['pageProps']['residenceDetails']['description']
    addressline_path = property_json['pageProps']['residenceDetails']['address']['displayAddress'] 
    residenceDetails_path = property_json['pageProps']['residenceDetails']['residenceOccupancies']
    
    amenities_path = property_json['pageProps']['residenceDetails']['features']
    services_path = property_json['pageProps']['residenceDetails']['facilities'] 
    
    #neighbourhoods_path = property_json['pageProps']['residenceDetails']['residenceOccupancies']
    #promocode_path = property_json['result'][0]['rental_discount']['rental_promo_code']
    
    # minimum_stay_path = property_json['result'][0]['center']['room']['basic']['minimum_stay']
    # extra_costs_path = property_json['result'][0]['center']['extra_costs_html']
    
    
    sharing_details ="Available sharing type and costs: "
    for i in residenceDetails_path: 
            if i['soldOut'] == False:
                one_sharing_details = i['occupancyName']+" rent actual price is "+str(i['startingPrice'])+", discounted price is "+str(i['discountedPrice'])+"."
                sharing_details += one_sharing_details  
      
     
    
    propertyname = "Property name: "+propertyname_path+".\n"
    address = "Address: "+addressline_path+".\n"
    clean = re.compile('<.*?>')
    description_clean = re.sub(clean, '', description_path).strip()+"\n\n"
    description_clean = description_clean.replace('&nbsp;',' ')
    description = "Description: "+description_clean+"\n\n"
    sharing_details =sharing_details+"\n\n"
   # promocode = "Promocode for the booking: "+promocode_path+".\n\n"
   # neighbourhoods = "Near by locations or highlights are as follows, "+neighbourhoods+".\n"
    
    amenities_details = [item['name'] for item in amenities_path] 
    amenities = "Available Amenities are "+', '.join(amenities_details)+".\n\n"  
    
    services_details = [item['name'] for item in services_path] 
    facilities = "Available Services are "+', '.join(services_details)+".\n\n"  
    
      
    #final_summary = propertyname+address+description+sharing_details+promocode+neighbourhoods+amenties+extra_cost+minimum_stay
    final_summary = propertyname+address+description+sharing_details+amenities+facilities
    print(final_summary)
    return final_summary
 


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)

# https://web.stanzaliving.com/cmsapi/website/food/get/menu/residence?transformationUuid=6ab9af27-ad3c-47e6-9df4-c139bb69893f