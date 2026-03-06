from dotenv import load_dotenv
import os
import requests
import logging
import json
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.messages import AIMessage
from fastapi import HTTPException

load_dotenv()

#get api_keys
api_key=os.getenv("Groq_api_key")
weather_api=os.getenv("weather_api")

Notes="notes.json"
task="task.json"

# weather tool
@tool
def get_weathers(query:str):
    """fatched current weather and temperature"""
    try:

        url=f"https://api.openweathermap.org/data/2.5/weather?q={query}&appid={weather_api}&units=imperial"
        response = requests.get(url)
        data = response.json()
        temperature = data["main"]["temp"]
        weather = data["weather"][0]["main"]
        logging.info("weather fatched!!")
        return {f"Current temperature is{temperature} and {weather}"}
    
    except:
        logging.error("weather not fatched!!")

# Notes tool   
@tool
def save_note(query):
    """Save the all Notes"""    
    try:
        if os.path.exists(Notes):
            with open(Notes,'r') as file:
                notes=json.load(file)
        else:
            notes=[]
            notes.append(query)
            with open(Notes,'w') as file:
                json.dump(notes,file)
            logging.info("Notes add")
        return "Note saved"
    except:
        logging.error("Notes not saved!!")
        
 
@tool
def get_notes():
    """show the Notes"""
    try:
        with open(Notes,'r') as file:
            show_nots=json.load(file)
            if not show_nots:
                return "Notes Not Found"
        logging.info("Notes show")
        return "\n".join(show_nots)
    
    except:
        logging.error("Notes Not show")
        HTTPException(status_code=500,detail="notes not found")

# Tasks tool
@tool
def add_task(query):
    """add all task"""
    try:
        if os.path.exists(task):
            with open(task,'r') as file:
                json.load(file)
        else:
            tasks=[]
            tasks.append({"task":query,"status":"pending"})
            with open(task, 'w') as file:
                json.dump(tasks,file,separators=',')
        logging.info("task add")
        return "Task added"
    except:
        logging.error("Task Not added!!")

@tool
def view_task():
    """view all tasks"""
    try:
        with open(task,'r') as file:
            get_task=json.load(file)
        if not get_task:
                return "Tasks Not Found"
        
        logging.info("Tasks show")
        return "\n".join(get_task)
    
    except Exception as e:
        print(e)
        logging.error("tasks not show")
        HTTPException(status_code=500,detail="tasks not found")


@tool
def complete_task(task):
    """complete task"""
    try:
        with open(task,'r') as file:
            mark_task=json.load(file)
        for task in mark_task:
            if task['status']=='Completed':
                break
                        
        with open(task, 'w') as file:
            json.dump(task, file, indent=4)

        return task
    except Exception as e:
        logging.error("task not complete")
        HTTPException(status_code=500,detail=str(e))

   
# llm model
model=ChatGroq(
    api_key=api_key,
    model="openai/gpt-oss-120b"
)

prompt=f"""
        - You are a helpful AI assistant.
        - you are follow the below rules.

        Rules:
        1. if user asked weather then you are calling get_weathers tool and return current weather with temperature.
        2. if user said add notes,you are calling save_note tool and saved all the data into json file,respond "Note saved"
        3. you are showing notes then called get_notes and return show all notes with number format.
        4. if you are add task then called add_task tool,respond "Task added".
        5. you are showing tasks then called view_task and return only show all tasks with number format.
        6. Do not give extra information.
        7.you are showing tasks complated then called complete_task and return show all complete task with number format.
"""

agent=create_agent(
    model=model,
    tools=[get_weathers,save_note,get_notes,add_task,view_task,complete_task],
    system_prompt=prompt
)

# call agent
def call_agent(query:str):
    response=agent.invoke({'messages': [AIMessage(query)]})
    return response