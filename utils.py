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

logger=logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
log=logging.getLogger(logger)

# weather tool
@tool
def get_weathers(query:str):
    """fatched current weather data"""
    try:

        url=f"https://api.openweathermap.org/data/2.5/weather?q={query}&appid={weather_api}&units=metric"
        response = requests.get(url)
        data = response.json()
        log.info("weather fatched!!")
        return data
    
    except:
        log.error("weather not fatched!!")
        return "unable to fatched weather" 

# Notes tool   
@tool
def save_note(query:str):
    """Save the all Notes"""    
    try:
        if os.path.exists(Notes) and os.path.getsize(Notes)>0 :
            with open(Notes,'r') as file:
                notes=json.load(file)
        else:
            notes=[]
        note_list=[t.strip() for t in query.split(",")] 
        for t in note_list:
            notes.append(t)
        with open(Notes,'w') as file:
            json.dump(notes,file)
        log.info("Notes add")
        return "Note saved"
    except:
        log.error("Notes not saved!!")
        return "Note Not Saved"
        
@tool
def show_notes():
    """show the Notes"""
    try:
        with open(Notes,'r') as file:
            show_nots=json.load(file)
        if not show_nots:
            return "Notes not Found"
        log.info("Notes show")
        return "\n".join(show_nots)
    
    except:
        log.error("Notes Not show")
        return "Notes not found"


# Tasks tool
@tool
def add_task(query:str):
    """add all task"""
    try:
        if os.path.exists(task) and os.path.getsize(task)>0:
            with open(task,'r') as file:
                tasks=json.load(file)
        else:
            tasks=[] 
        task_list=[t.strip() for t in query.split(",")] 
        for t in task_list:
            new_task={"task":t,"status":"Pending"}
            tasks.append(new_task)
     
        with open(task, 'w') as file:
                json.dump(tasks,file,indent=4)
        log.info("Task add")
        return "Task added"
    except:
        log.error("Task Not added!!")
        return "tasks not added"

@tool
def view_task():
    """view all tasks"""
    try:
        with open(task,'r') as file:
            get_task=json.load(file)
        if not get_task:
            return "Tasks not Found"
        
        result=" "
        for i,t in enumerate(get_task,start=1):
            result += f"{i}. {t['task']} ({t['status']})\n"
        
        log.info("Tasks show")
        return result
    
    except:
        log.error("tasks not show")
        return "Tasks not found"
     
@tool       
def complete_task(index:int):
    """update the task complete"""
    try:
        with open(task, "r") as f:
            tasks_update = json.load(f)
        
        if index<1 or index >len(tasks_update):
            return "Invalid task index"
        
        tasks_update[index-1]["status"] = "Completed"
        
        
        with open(task, "w") as f:
            json.dump(tasks_update, f)
        log.info("task updated")
        return "Task marked as completed."
        

    except:
        log.error("task not updated")
        return "Invalid task index."


# llm model
model=ChatGroq(
    api_key=api_key,
    model="openai/gpt-oss-120b"
)

prompt=f"""
        - You are a helpful AI assistant.
        - you are follow the below rules.

        Rules:
        1. if user ask weather details then you are call get_weathers tool and return all current weather data.
        2. if user ask add notes,you are call save_note tool and saved all the data into json file,respond "Note saved".
        3. if you are showing notes then call show_notes and  Return only the all final answer with number format.
        4. if user add multiple task or note then add one by one in json.
        5. When the user asks to show tasks, call the view_task tool and return the tool output exactly as received with no extra text and format changes.
        6. If the user asks to complete or update a task, identify the index number and call the complete_task tool.
        7. Do not give extra information.
        8. Do not explain reasoning.
        9. Do not show which tool you used.
        10.Do not give answer except notes,weather and task.
        11.if user asks showing both task and notes,then response 
            i) Tasks:
                - show task all final answer.
            ii) Notes:
                - show notes all final answer. 
        12.If the user asks to complete or update a task,convert text number into numeric number.
        """

agent=create_agent(
    model=model,
    tools=[get_weathers,save_note,show_notes,add_task,view_task,complete_task],
    system_prompt=prompt
)


# call agent
@traceable(name="call_agent")
def call_agent(query:str):
    try:
        response=agent.invoke({'messages': [HumanMessage(content=query)]})
        return response
    except Exception as e:
        logging.error("Sorry, I am facing an issue. Please try again")
        raise HTTPException(status_code=500,detail=str(e))

