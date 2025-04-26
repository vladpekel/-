from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, field_validator, constr
from typing import List
from contextlib import asynccontextmanager
from datetime import date
import sqlite3
import uvicorn
import bcrypt
import hashlib
import os
from dotenv import load_dotenv

load_dotenv('.env')
app = FastAPI()


def init_db():
    with sqlite3.connect('bookings.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL CHECK(length(phone) >= 10),
                age INTEGER NOT NULL CHECK(age >= 14),
                date TEXT NOT NULL,
                attractions TEXT NOT NULL
            )
        ''')
        conn.commit()
    conn.close()


init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
app = FastAPI(lifespan=lifespan)
security = HTTPBasic()


class Booking(BaseModel):
    name: str
    phone: constr(pattern=r'^\d{10,15}$')  # Только цифры, 10-15 символов
    age: int
    date: date
    attractions: List[str]

    @field_validator('age')
    def validate_age(cls, v):
        if v < 14:
            raise ValueError('Minimum age is 14')
        return v


@app.post("/book")
def create_booking(booking: Booking):
    try:
        with sqlite3.connect('bookings.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO bookings (name, phone, age, date, attractions)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                booking.name,
                booking.phone,
                booking.age,
                booking.date.isoformat(),
                ','.join(booking.attractions)
            ))
            conn.commit()
        return {"status": "ok"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bookings")
def get_bookings():
    with sqlite3.connect('bookings.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM bookings')
        return [
            {
                "id": row['id'],
                "name": row['name'],
                "phone": row['phone'],
                "age": row['age'],
                "date": row['date'],
                "attractions": row['attractions'].split(',')
            }
            for row in cursor.fetchall()
        ]


@app.delete("/bookings")
def delete_bookings():
    with sqlite3.connect('bookings.db') as conn:
        conn.execute('DELETE FROM bookings')
        conn.commit()
    return {"message": "All bookings deleted"}


@app.delete("/bookings/{booking_id}")
def delete_booking_id(booking_id: int):
    with sqlite3.connect('bookings.db') as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM bookings WHERE id = ?",
            (booking_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Бронирование не найдено")
        conn.commit()
    return {"message": f"Booking {booking_id} deleted"}


@app.put("/bookings/{booking_id}")
def update_booking(booking_id: int, booking: Booking):
    try:
        with sqlite3.connect('bookings.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bookings
                SET name = ?,
                    phone = ?,
                    age = ?,
                    date = ?,
                    attractions = ?
                WHERE id = ?
            ''', (
                booking.name,
                booking.phone,
                booking.age,
                booking.date.isoformat(),
                ','.join(booking.attractions),
                booking_id
            ))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Бронирование не найдено")
            conn.commit()
        return {"status": "updated"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/admin")
def admin_auth(credentials: HTTPBasicCredentials = Depends(security)):
    try:
        print(f"Auth attempt with password: {credentials.password}")

        stored_hash = os.getenv("ADMIN_PASSWORD_HASH")
        if not stored_hash:
            print("Error: ADMIN_PASSWORD_HASH not set in .env")
            raise HTTPException(status_code=500, detail="Server configuration error")

        # Проверка хеша
        password_bytes = credentials.password.encode('utf-8')
        stored_hash_bytes = stored_hash.encode('utf-8')

        print(f"Stored hash: {stored_hash}")
        print(f"Password hash: {bcrypt.hashpw(password_bytes, stored_hash_bytes)}")

        if bcrypt.checkpw(password_bytes, stored_hash_bytes):
            print("Authentication successful")
            return {"status": "ok"}

        print("Invalid password")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Переменные окружения:")
    print("ADMIN_PASSWORD_HASH:", os.getenv("ADMIN_PASSWORD_HASH"))
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
