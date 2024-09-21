import sqlite3
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import asyncio
from LocationFinder import *
import json
import os

app = FastAPI()
db_path = os.path.join('..', 'DB', 'Colive.db')


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
    url = 'https://api.zolostays.com/api/v2/center/pdp?zolo_code='+property_id
    print(property_id)   
    x = requests.get(url)
    final_answer = x.json() 
    extract_metadata(final_answer)
    return final_answer

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
        url = 'http://127.0.0.1:8001/filter'
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)


def extract_metadata(property_json): 
    description_path = property_json['result'][0]['center']['description']
    amenities_path = property_json['result'][0]['center']['amenities']
    neighbourhoods_path = property_json['result'][0]['center']['neighborhood']
    #promocode_path = property_json['result'][0]['rental_discount']['rental_promo_code']
    room_path = property_json['result'][0]['center']['room']['sharings']
    minimum_stay_path = property_json['result'][0]['center']['room']['basic']['minimum_stay']
    extra_costs_path = property_json['result'][0]['center']['extra_costs_html']
    propertyname_path = property_json['result'][0]['center']['name']
    addressline1_path = property_json['result'][0]['center']['address_line1']
    addressline2_path = property_json['result'][0]['center']['address_line2']
    sharing_details ="Available sharing type and costs: "
    for i in room_path:
        if i['sharing'] == 1:
            if i['available'] == 1:
                one_sharing_details = "One sharing rents are "+i['rent']+"."
                sharing_details += one_sharing_details 
        if i['sharing'] == 2:
            if i['available'] == 1:
                two_sharing_details = "Two sharing rents are "+i['rent']+"." 
                sharing_details += two_sharing_details
        if i['sharing'] == 3:
            if i['available'] == 1:
                three_sharing_details = "Three sharing rents are "+i['rent']+"." 
                sharing_details += three_sharing_details
        if i['sharing'] == 4:
            if i['available'] == 1:
                four_sharing_details = "Four sharing rents are "+i['rent']+"." 
                sharing_details += four_sharing_details
        if i['sharing'] == 5:
            if i['available'] == 1:
                five_sharing_details = "Five sharing rents are "+i['rent']+"." 
                sharing_details += five_sharing_details
        if i['sharing'] == 6:
            if i['available'] == 1:
                six_sharing_details = "Six sharing rents are "+i['rent']+"."
                sharing_details += six_sharing_details
      
    
    combined_details = [
    f"{item['title']} in {item['distance']} reach by {item['time']}"
    for item in neighbourhoods_path if item['title']  # Skip empty titles
    ]

    # Join with a newline for better readability
    neighbourhoods = '\n'.join(combined_details)
    
    
    propertyname = "Property name: "+propertyname_path+".\n"
    address = "Address: "+addressline1_path+addressline2_path+".\n"
    description = "Description: "+description_path+".\n\n"
    sharing_details =sharing_details+"\n\n"
   # promocode = "Promocode for the booking: "+promocode_path+".\n\n"
    neighbourhoods = "Near by locations or highlights are as follows, "+neighbourhoods+".\n"
    amenties_available_details = [item['title'] for item in amenities_path if item['availability'] == 1] 
    amenties = "Available Amenties are "+', '.join(amenties_available_details)+".\n\n"  
    clean = re.compile('<.*?>')
    extra_cost = re.sub(clean, '', extra_costs_path).strip()+".\n\n"
    extra_cost = extra_cost.replace('&nbsp;','')
    minimum_stay = "Minimum stay or lockin period of the property is "+minimum_stay_path+".\n"
     
    #final_summary = propertyname+address+description+sharing_details+promocode+neighbourhoods+amenties+extra_cost+minimum_stay
    final_summary = propertyname+address+description+sharing_details+neighbourhoods+amenties+extra_cost+minimum_stay
    print(final_summary)
    return final_summary