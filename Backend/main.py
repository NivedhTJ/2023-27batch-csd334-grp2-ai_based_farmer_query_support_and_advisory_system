import os
import io
import numpy as np
import requests
from PIL import Image
import tensorflow as tf
from tensorflow import keras  # type:ignore
from tensorflow.keras import layers, models  # type:ignore
import mysql.connector
import ollama
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Farmer Query Support")

WEATHER_API_KEY = "" 
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLASSES = [
    'Apple_scab', 'Apple_black_rot', 'Apple_cedar_apple_rust', 'Apple_healthy',
    'Background_without_leaves', 'Blueberry_healthy', 'Cherry_powdery_mildew',
    'Cherry_healthy', 'Corn_gray_leaf_spot', 'Corn_common_rust',
    'Corn_northern_leaf_blight', 'Corn_healthy', 'Grape_black_rot',
    'Grape_black_measles', 'Grape_leaf_blight', 'Grape_healthy',
    'Orange_haunglongbing', 'Peach_bacterial_spot', 'Peach_healthy',
    'Pepper_bacterial_spot', 'Pepper_healthy', 'Potato_early_blight',
    'Potato_healthy', 'Potato_late_blight', 'Raspberry_healthy',
    'Soybean_healthy', 'Squash_powdery_mildew', 'Strawberry_healthy',
    'Strawberry_leaf_scorch', 'Tomato_bacterial_spot', 'Tomato_early_blight',
    'Tomato_healthy', 'Tomato_late_blight', 'Tomato_leaf_mold',
    'Tomato_septoria_leaf_spot', 'Tomato_spider_mites_two-spotted_spider_mite',
    'Tomato_target_spot', 'Tomato_mosaic_virus', 'Tomato_yellow_leaf_curl_virus'
]

def load_farmer_model():
    preprocess_input = keras.applications.mobilenet_v2.preprocess_input
    base_model = keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    model = models.Sequential([
        layers.Input(shape=(224, 224, 3)),
        layers.Lambda(preprocess_input),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(len(CLASSES), activation='softmax')
    ])

    if os.path.exists('models/trained_farmer_model.h5'):
        model.load_weights('models/trained_farmer_model.h5')

    return model

MODEL = load_farmer_model()

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="farmer_ai"
    )

def get_weather(location: str):
    try:
        if not WEATHER_API_KEY:
            print("Weather API key not set.")
            return None

        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }

        response = requests.get(WEATHER_BASE_URL, params=params, timeout=10)

        if response.status_code != 200:
            print("Weather API error:", response.status_code, response.text)
            return None

        data = response.json()

        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"],
            "wind_speed": data["wind"]["speed"]
        }
        

    except Exception as e:
        print("Weather fetch exception:", str(e))
        return None

class LoginRequest(BaseModel):
    username: str
    password: str

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
        "user_id": user["id"],
        "username": user["username"]
    }

@app.get("/sessions/{user_id}")
async def get_sessions(user_id: int):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT session_id, user_query as title 
            FROM chat_history 
            WHERE user_id = %s 
            AND query_id IN (
                SELECT MIN(query_id) 
                FROM chat_history 
                GROUP BY session_id
            )
            ORDER BY query_id DESC
            """,
            (user_id,)
        )

        sessions = cursor.fetchall()
        cursor.close()
        db.close()
        return {"sessions": sessions}

    except Exception as e:
        print(f"Session Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/{user_id}")
async def get_user_weather(user_id: int):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT location FROM users WHERE id=%s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if not result or not result["location"]:
            return {"weather": None, "message": "Location not found for user"}

        location = result["location"]
        weather = get_weather(location)

        if not weather:
            return {"weather": None, "message": "Failed to fetch weather data"}

        return {"weather": weather, "location": location}

    except Exception as e:
        print(f"Weather Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_query, ai_response FROM chat_history WHERE session_id=%s ORDER BY query_id ASC",
            (session_id,)
        )

        history = cursor.fetchall()
        cursor.close()
        db.close()
        return {"history": history}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clear/{user_id}")
async def clear_history(user_id: int):
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("DELETE FROM chat_history WHERE user_id=%s", (user_id,))
        db.commit()

        cursor.close()
        db.close()

        return {"success": True, "message": "History cleared"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class LocationUpdate(BaseModel):
    location: str

@app.put("/users/{user_id}/location")
async def update_location(user_id: int, request: LocationUpdate):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE users SET location=%s WHERE id=%s", (request.location, user_id))
        db.commit()
        cursor.close()
        db.close()
        return {"success": True, "message": "Location updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

@app.put("/users/{user_id}/password")
async def update_password(user_id: int, request: PasswordUpdate):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if not user or user["password"] != request.old_password:
            cursor.close()
            db.close()
            raise HTTPException(status_code=401, detail="Incorrect current password")

        cursor.execute("UPDATE users SET password=%s WHERE id=%s", (request.new_password, user_id))
        db.commit()
        cursor.close()
        db.close()
        return {"success": True, "message": "Password updated successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_farmer_bot(
    user_id: int = Form(...),
    session_id: str = Form(...),
    query: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        diagnosis = ""
        user_input = query or "Say how can I help you."

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT location FROM users WHERE id=%s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        location = result["location"] if result else None

        if file:
            img_data = await file.read()
            img = Image.open(io.BytesIO(img_data)).convert("RGB").resize((224, 224))
            img_array = np.array(img).astype('float32')
            img_array = np.expand_dims(img_array, axis=0)

            preds = MODEL.predict(img_array)
            diagnosis = CLASSES[np.argmax(preds)]
            user_input = f"The plant is diagnosed with {diagnosis}. {user_input}"

        weather_context = ""
        weather_used = False

        if location:
            weather = get_weather(location)
            if weather:
                weather_used = True
                weather_context = (
                    f"Current weather in {location}: "
                    f"{weather['temperature']}°C, "
                    f"{weather['description']}, "
                    f"Humidity {weather['humidity']}%, "
                    f"Wind speed {weather['wind_speed']} m/s. "
                )

        full_prompt = weather_context + user_input

        response = ollama.chat(
            model="gemma3:1b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional agronomist. Use weather context if available. If no weather data is provided, do NOT assume any weather conditions. Keep advice under 120 words."
                },
                {"role": "user", "content": full_prompt}
            ]
        )

        ai_msg = response["message"]["content"]

        db = get_db()
        cursor = db.cursor()

        db_query_text = query if query else f"Scan: {diagnosis}"

        cursor.execute(
            "INSERT INTO chat_history (user_id, session_id, user_query, ai_response) VALUES (%s, %s, %s, %s)",
            (user_id, session_id, db_query_text, ai_msg)
        )

        db.commit()
        cursor.close()
        db.close()

        return {
            "response": ai_msg,
            "detected": diagnosis if file else None,
            "weather_used": weather_used
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class FeedbackRequest(BaseModel):
    name: str
    mobile: str
    category: str
    rating: int
    feedback: str

@app.post("/submit-feedback")
async def submit_feedback(request: FeedbackRequest):
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO feedback (name, mobile, category, rating, feedback)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (request.name, request.mobile, request.category, request.rating, request.feedback)
        )

        db.commit()
        cursor.close()
        db.close()

        return {"success": True, "message": "Feedback submitted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/stats")
async def get_admin_stats():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        users_count = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) as total_queries FROM chat_history")
        queries_count = cursor.fetchone()["total_queries"]

        cursor.close()
        db.close()
        return {"total_users": users_count, "total_queries": queries_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users")
async def get_admin_users():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        # Fetching all users, excluding passwords for security
        cursor.execute("SELECT id, username, location FROM users ORDER BY id DESC")
        users = cursor.fetchall()
        
        cursor.close()
        db.close()
        return {"users": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/recent-queries")
async def get_admin_recent_queries():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        query = """
            SELECT c.query_id as timestamp, c.user_query, u.username, u.location 
            FROM chat_history c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.query_id DESC
            LIMIT 50
        """
        cursor.execute(query)
        recent_queries = cursor.fetchall()

        cursor.close()
        db.close()
        return {"queries": recent_queries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))