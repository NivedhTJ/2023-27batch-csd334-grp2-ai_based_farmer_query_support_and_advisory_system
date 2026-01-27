from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import ollama

app = FastAPI(title="AI Farmer Query Support")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="farmer_ai"
    )

class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    user_id: int  
    query: str

@app.post("/login")
async def login(request: LoginRequest):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, username FROM users WHERE username=%s AND password=%s",
        (request.username, request.password)
    )
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "success": True, 
        "message": "Login successful",
        "user_id": user["id"]
    }

@app.post("/ask")
async def ask_farmer_bot(request: QueryRequest):
    try:
        system_prompt = (
            "Limit responses to 100 words. "
            "You are an expert agricultural assistant. "
            "Provide simple, practical advice for farmers."
        )

        response = ollama.chat(
            model="gemma3:1b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ]
        )
        
        ai_msg = response["message"]["content"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO chat_history (user_id, user_query, ai_response) VALUES (%s, %s, %s)",
            (request.user_id, request.query, ai_msg)
        )
        db.commit()
        cursor.close()
        db.close()

        return {"response": ai_msg}

    except Exception as e:
        print("AI/DB error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")