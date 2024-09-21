from langchain.chains.api.base import _check_in_allowed_domain
from langchain_community.llms import Ollama
from langchain.chains import LLMChain, APIChain
from langchain.memory.buffer import ConversationBufferMemory
import re
from dotenv import load_dotenv
from io import BytesIO

import chainlit as cl
import requests
import json
import webbrowser
load_dotenv()

selected_PropertyID = ""
property_json = {} 
selected_PropertyName = ""


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

@cl.action_callback("action_cancel")
async def on_action(action: cl.Action):
    global selected_PropertyID, selected_PropertyName
    selected_PropertyID = ""
    selected_PropertyName = ""
    print("selected_PropertyID cleared"+selected_PropertyID)



@cl.action_callback("action_open")
async def on_action(action: cl.Action):
    global property_json, selected_PropertyID, selected_PropertyName
    
    print(action.value)
    selected_PropertyName = action.description
    # webbrowser.open(action.value)
    propertyID = action.value.replace('https://www.stanzaliving.com/',"") 
    print("Step1")
    print(propertyID)
    propertyID = propertyID.replace('/','%2')
    print("Step2")
    print(propertyID)
    selected_PropertyID = propertyID
    url = 'http://127.0.0.1:8002/getPropertyDetails/' + propertyID
    x = requests.get(url)
    print(x)
    final_answer = x.json()
    print(final_answer) 
    property_json = final_answer
    extract_metadata(property_json)
    
    await cl.Message("Please ask the question about the "+selected_PropertyName).send()
    actions = [
        cl.Action(name="action_cancel", label="cancel",
                  value="cancel", description="Cancel")
    ]

    await cl.Message(content="To check other properties, Click cancel button", actions=actions).send()
    return "Thank you for clicking on the action button!"


@cl.on_message
async def handle_message(message: cl.Message):
    global selected_PropertyID
    
    if len(selected_PropertyID) == 0:
        print(message)
        properties = ""
        user_message = message.content.lower()
        url = 'http://127.0.0.1:8002/find'
        myobj = {"query": user_message}
        x = requests.post(url, json=myobj)

        final_answer = x.json()
        print(final_answer)

        response = final_answer 
        actions = []
        for i in response:
            properties += i['name']+"\n"
            actions.append(
            cl.Action(name= "action_open",
                    label=i['name'],
                    value="https://www.stanzaliving.com/"+i["citySlug"]+"/"+i["micromarketSlug"]+"/"+i["gender"]+"/"+i["slug"], description=i['name']))

        await cl.Message(content="Matching results:", actions=actions).send() 
    else:  
        print("selected_PropertyID")
        print(selected_PropertyID)
        global property_json
        final_summary = extract_metadata(property_json)
        
        url = 'http://localhost:11434/api/generate'
        myobj = {"model": "llama3", "stream": False, "prompt": "'''Your name is Swetha, your role is real estate assistant, This is summary of the property:"+str(final_summary)
                                                            +".You have to answer following the query. Show the results as simple. \n\nQuery :" + message.content.lower() + ".'''"}
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