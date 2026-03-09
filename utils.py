from dotenv import load_dotenv
import os
import requests
import logging
import json
from langchain.tools import tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage
from fastapi import HTTPException
from langsmith import traceable

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

        url=f"https://api.openweathermap.org/data/2.5/weather?q={query}&appid={weather_api}&units=metric"
        response = requests.get(url)
        data = response.json()
        temperature = data["main"]["temp"]
        weather = data["weather"][0]["main"]
        logging.info("weather fatched!!")
        return {f"Current temperature is{temperature} and {weather}"}
    
    except:
        logging.error("weather not fatched!!")
        return "unable to fatched weather"

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
        return "Note Not Saved"
        

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
        raise HTTPException(status_code=500,detail="notes not found")

# Tasks tool
@tool
def add_task(query):
    """add all task"""
    try:
        if os.path.exists(task):
            with open(task,'r') as file:
                tasks=json.load(file)
        else:
            tasks=[]
        new_task={"task":query,"status":"Pending"}
        tasks.append(new_task)
        with open(task, 'w') as file:
            json.dump(tasks,file)
        logging.info("task add")
        return "Task added"
    except:
        logging.error("Task Not added!!")
        raise HTTPException(status_code=500,detail="tasks not added")


@tool
def view_task():
    """view all tasks"""
    try:
        with open(task,'r') as file:
            get_task=json.load(file)
        if not get_task:
                return "Tasks Not Found"
        
        result=" "
        for i,t in enumerate(get_task,start=1):
            result += f"{i}. {t['task']} ({t['status']})"

        logging.info("Tasks show")
        return result
    
    except:
        logging.error("tasks not show")
        raise HTTPException(status_code=500,detail="tasks not found")


@tool
def complete_task(index:int):
    """complete or update tasks"""
    try:
        with open(task,'r') as file:
            mark_task=json.load(file)
        mark_task[index-1]['status']=='Completed'
        with open(task,'w') as f:
            json.dump(mark_task,f)
        logging.info("Task updated")       
        return "Task marked as completed."
    except:
        logging.error("task not complete")
        raise HTTPException(status_code=500,detail="tasks not completed")
        


# llm model
model=ChatGroq(
    api_key=api_key,
    model="openai/gpt-oss-120b"
)

prompt=f"""
        - You are a helpful AI assistant.
        - you are follow the below rules.

        Rules:
        1. if user ask weather then you are call get_weathers tool and return current weather with temperature.
        2. if user ask add notes,you are call save_note tool and saved all the data into json file,respond "Note saved".
        3. if you are showing notes then call get_notes and  Return only the all final answer with number format.
        4. if you are add task then called add_task tool,respond only "Task added".
        5. When the user asks to show tasks, call the view_task tool and return the tool output exactly as received with no extra text and format changes.
        6. If the user asks to complete or update a task, identify the task number and call the complete_task tool with the index, then return "Task marked as completed."
        7. Do not give extra information.
        8. Do not explain reasoning.
        9. Do not show which tool you used.
        """

agent=create_agent(
    model=model,
    tools=[get_weathers,save_note,get_notes,add_task,view_task,complete_task],
    system_prompt=prompt
)

# call agent
def call_agent(query:str):
    response=agent.invoke({'messages': [HumanMessage(content=query)]})
    return response