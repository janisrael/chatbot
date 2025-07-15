from db_model import get_connection

def setup():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SET FOREIGN_KEY_CHECKS=0")

    # Create chat_logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INT PRIMARY KEY AUTO_INCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_id VARCHAR(100),
        message TEXT NOT NULL,
        sender ENUM('user', 'bot') NOT NULL,
        sales_flag VARCHAR(50),
        success_flag ENUM('Yes', 'No') DEFAULT 'No',
        intent VARCHAR(50), 
        context_snapshot TEXT
    )
    """)

    # Ensure the success_flag column exists in case of schema changes
    cursor.execute("""
    ALTER TABLE chat_logs
    ADD COLUMN IF NOT EXISTS success_flag ENUM('Yes', 'No') DEFAULT 'No';
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration complete, Database Created!")

if __name__ == "__main__":
    setup()
