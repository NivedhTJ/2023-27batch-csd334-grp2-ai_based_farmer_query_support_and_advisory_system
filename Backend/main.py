import os
import io
import numpy as np
from PIL import Image
import tensorflow as tf
from tensorflow import keras #type:ignore
from tensorflow.keras import layers, models #type:ignore
import mysql.connector
import ollama
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Farmer Query Support")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plant Disease Classes
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
    """Loads the MobileNetV2-based plant disease classifier."""
    preprocess_input = keras.applications.mobilenet_v2.preprocess_input
    base_model = keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    base_model.trainable = False

    m = models.Sequential([
        layers.Input(shape=(224, 224, 3)),
        layers.Lambda(preprocess_input),
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(len(CLASSES), activation='softmax')
    ])

    if os.path.exists('models/trained_farmer_model.h5'):
        m.load_weights('models/trained_farmer_model.h5')

    return m

MODEL = load_farmer_model()

def get_db():
    """Establishes connection to MySQL database."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="farmer_ai"
    )

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

@app.post("/ask")
async def ask_farmer_bot(
    user_id: int = Form(...),
    session_id: str = Form(...),
    query: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        diagnosis = ""
        user_input = query or "Provide agricultural advice."

        if file:
            img_data = await file.read()
            img = Image.open(io.BytesIO(img_data)).resize((224, 224))
            img_array = np.array(img).astype('float32')
            img_array = np.expand_dims(img_array, axis=0)

            preds = MODEL.predict(img_array)
            diagnosis = CLASSES[np.argmax(preds)]
            user_input = f"The plant is diagnosed with {diagnosis}. {user_input}"

        # Get AI Response
        response = ollama.chat(
            model="gemma3:1b",
            messages=[
                {"role": "system", "content": "You are a professional agronomist. Keep advice under 120 words."},
                {"role": "user", "content": user_input}
            ]
        )

        ai_msg = response["message"]["content"]

        # Save to Database
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
            "detected": diagnosis if file else None
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))