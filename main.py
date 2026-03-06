from fastapi import FastAPI,HTTPException
from utils import call_agent
from fastapi.responses import JSONResponse

app=FastAPI()

@app.get("/")
def msg():
    return {"message":"fastapi is working..."}

@app.post("/ask query/")
def get_query(query:str):
    try:
        response=call_agent(query)
        answer=response.get('messages')[-1].content
        return JSONResponse({"answer":answer})
    
    except Exception as e:
        HTTPException(status_code=404,detail=str(e))

