from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ollama

app = FastAPI(title="AI Farmer Query Support")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS = {
    "farmer1": "password123",
    "admin": "adminpass"
}

class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str

@app.post("/login")
async def login(request: LoginRequest):
    if request.username in USERS and USERS[request.username] == USERS[request.username]:
        return {"success": True, "message": "Login successful!"}
    elif request.username in USERS and USERS[request.username] != USERS[request.username]:
        return {"success": False, "message": "Incorrect password!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/ask")
async def ask_farmer_bot(request: QueryRequest):
    try:
        system_prompt = (
            "Limit responses to 50 words"
            "You are an expert agricultural assistant. "
            "Provide simple, practical advice for farmers."
        )

        response = ollama.chat(
            model="llama3.2:1b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ]
        )

        return {"response": response["message"]["content"]}

    except Exception as e:
        print("AI error:", e)
        raise HTTPException(status_code=500, detail="AI service error")