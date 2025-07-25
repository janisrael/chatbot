import mysql.connector
from datetime import datetime

from db_config import DB_CONFIG

# db_config.py


def log_chat(user_id, message, sender, intent=None, sales_flag=None, success_flag=None):
    try:
        # Establish the connection
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Ensure connection is established
        if connection.is_connected():
            # Current timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Default values for sales_flag and success_flag
            if sales_flag is None:
                sales_flag = 0  # Default to 0 (No sales intent)

            if success_flag is None:
                success_flag = 1 if intent == "sales" else 0

            # Insert data into the database
            query = """INSERT INTO chat_logs (timestamp, user_id, message, sender, intent, sales_flag, success_flag)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(query, (timestamp, user_id, message, sender, intent, sales_flag, success_flag))

            # Commit the transaction
            connection.commit()

            print("Chat logged successfully!")

        else:
            print("Connection to database failed.")

    except mysql.connector.Error as e:
        print(f"Error logging chat: {e}")

    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_or_create_user(name, email, phone):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        cursor.close()
        conn.close()
        return user["id"]

    cursor.execute("INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
    conn.commit()
    user_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return user_id


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)