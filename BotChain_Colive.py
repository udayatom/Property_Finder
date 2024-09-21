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


@cl.action_callback("action_open")
async def on_action(action: cl.Action):
    print(action.value)
    webbrowser.open(action.value)
    return "Thank you for clicking on the action button!"


@cl.on_message
async def handle_message(message: cl.Message):
    print(message)
    properties = ""
    user_message = message.content.lower()
    url = 'http://127.0.0.1:8001/find'
    myobj = {"query": user_message}
    x = requests.post(url, json=myobj)

    final_answer = x.json()
    print(final_answer)

    response = final_answer 
    actions = []
    for i in response:
        properties += i['locationName']+"\n"
        actions.append(
        cl.Action(name= "action_open",
                  label=i['locationName'],
                  value="https://www.colive.com/property/"+i["propertyLink"], description=i['locationName']))

    await cl.Message(content="Matching results:", actions=actions).send() 
    # await cl.Message(properties).send()
