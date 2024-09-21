from langchain.chains.api.base import _check_in_allowed_domain
from langchain_community.llms import Ollama
from langchain.chains import LLMChain, APIChain
from langchain.memory.buffer import ConversationBufferMemory

from dotenv import load_dotenv
from io import BytesIO

import chainlit as cl
import requests
import json
import webbrowser
import re

load_dotenv()

#
# @cl.on_chat_start
# def setup_multiple_chains():
#

# @cl.on_audio_chunk
# async def on_audio_chunk(chunk: cl.AudioChunk):
#     if chunk.isStart:
#         buffer = BytesIO()
#         # This is required for whisper to recognize the file type
#         buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
#         # Initialize the session for a new audio stream
#         cl.user_session.set("audio_buffer", buffer)
#         cl.user_session.set("audio_mime_type", chunk.mimeType)

#     # Write the chunks to a buffer and transcribe the whole audio at the end
#     cl.user_session.get("audio_buffer").write(chunk.data)

selected_PropertyID = ""
property_json = {} 
selected_PropertyName = ""



@cl.action_callback("action_cancel")
async def on_action(action: cl.Action):
    global selected_PropertyID
    selected_PropertyID = ""
    print("selected_PropertyID cleared"+selected_PropertyID)


@cl.action_callback("action_open")
async def on_action(action: cl.Action):
    global property_json, selected_PropertyID
    
    print(action.value)
    # webbrowser.open(action.value)
    propertyID = action.value.split('=')[1] 
    selected_PropertyID = propertyID
    url = 'http://127.0.0.1:8003/getPropertyDetails/' + propertyID
    x = requests.get(url)
    print(x)
    final_answer = x.json()
    print(final_answer) 
    property_json = final_answer
    extract_metadata(property_json)
    
    await cl.Message("Please ask the question about the "+selected_PropertyID).send()
    actions = [
        cl.Action(name="action_cancel", label="cancel",
                  value="cancel", description="Cancel")
    ]

    await cl.Message(content="To cancel, Click cancel button", actions=actions).send()
    return "Thank you for clicking on the action button!"


@cl.on_message
async def handle_message(message: cl.Message):
    global selected_PropertyID
    
    if len(selected_PropertyID) == 0:
        print(message)
        properties = ""
        user_message = message.content.lower()
        url = 'http://127.0.0.1:8003/find'
        myobj = {"query": user_message}

        x = requests.post(url, json=myobj)

        final_answer = x.json()
        print(final_answer)

        response = final_answer
        actions = []
        for i in response:
            properties += i['propertyname']+"\n"
            actions.append(
                cl.Action(name="action_open",
                          label=i['propertyname'],
                          value="https://zolostays.com/pg/?zoloCode="+i["propertyLink"], description=i['propertyname']))

        await cl.Message(content="Matching results:", actions=actions).send()

    else:
         
        print("selected_PropertyID")
        print(selected_PropertyID )
        global property_json
        final_summary = extract_metadata(property_json)
        
        url = 'http://localhost:11434/api/generate'
        myobj = {"model": "llama3", "stream": False, "prompt": "'''Your name is Swetha, your role is real estate assistant, This is summary of the property:"+str(final_summary)
                                                            +".You have to answer following the query. \n\nQuery :" + message.content.lower() + ".'''"}
        print(myobj)
        x = requests.post(url, json=myobj)

        final_answer = x.json()

        print(final_answer["response"])
            
        await cl.Message(content= final_answer["response"]).send()
        actions = [
        cl.Action(name="action_cancel", label="cancel",
                  value="cancel", description="Cancel")
        ]

        await cl.Message(content="To check other properties, Click cancel button", actions=actions).send()

    # await cl.Message(properties).send()


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