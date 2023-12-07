import sqlite3

# Connect to SQLite database (this will create the database file if it does not exist)
conn = sqlite3.connect('users.db')

# Create a cursor object using the cursor() method
cursor = conn.cursor()

# SQL query to create a 'users' table
create_users_table_query = '''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL
                        );'''

# SQL query to create an 'orders' table
create_orders_table_query = '''CREATE TABLE IF NOT EXISTS orders (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                customer_id INTEGER NOT NULL,
                                order_datetime DATETIME NOT NULL,
                                delivery_datetime DATETIME NOT NULL,
                                box_count INTEGER NOT NULL,
                                box_contents TEXT,
                                dropoff_location TEXT,
                                additional_comments TEXT,
                                venmo_username TEXT,
                                deliverer_id INTEGER,
                                order_price REAL,
                                FOREIGN KEY (customer_id) REFERENCES users (id),
                                FOREIGN KEY (deliverer_id) REFERENCES users (id)
                            );'''

# Execute the SQL commands to create both tables
cursor.execute(create_users_table_query)
cursor.execute(create_orders_table_query)

# Commit changes in the database
conn.commit()

# Close the connection
conn.close()

print("Database and tables created successfully.")
