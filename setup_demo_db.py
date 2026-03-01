"""
Database Setup Script
Creates a SQLite demo database with sample data for the dashboard application.
Originally designed to work with remote MySQL, now uses local SQLite for demo purposes.
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "demo_dashboard.db"

def create_database():
    """Create SQLite database and tables with realistic column names"""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()
    
    # Create manage_users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manage_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            pass TEXT NOT NULL,
            type TEXT DEFAULT 'all',
            last_login TEXT,
            last_logout TEXT
        )
    """)
    
    # Create user_subscriptions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_account TEXT NOT NULL,
            target_account TEXT NOT NULL,
            period INTEGER NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            date TEXT NOT NULL,
            update_date TEXT,
            last_login TEXT,
            added_by TEXT,
            updated_by TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    
    # Create account_migrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_account TEXT NOT NULL,
            target_account TEXT NOT NULL,
            period INTEGER NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            date TEXT NOT NULL,
            update_date TEXT,
            last_login TEXT,
            added_by TEXT,
            updated_by TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    
    # Create subscription_mappings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscription_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_account TEXT NOT NULL,
            target_account TEXT NOT NULL,
            period INTEGER NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            date TEXT NOT NULL,
            update_date TEXT,
            user_id TEXT,
            last_login TEXT,
            added_by TEXT,
            updated_by TEXT,
            balance REAL DEFAULT 0.0
        )
    """)
    
    # Create dual_subscription_mappings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dual_subscription_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_account TEXT NOT NULL,
            target_account TEXT NOT NULL,
            period INTEGER NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            date TEXT NOT NULL,
            update_date TEXT,
            source_user_id TEXT,
            target_user_id TEXT,
            last_login TEXT,
            added_by TEXT,
            updated_by TEXT,
            source_balance REAL DEFAULT 0.0,
            target_balance REAL DEFAULT 0.0
        )
    """)
    
    connection.commit()
    return connection, cursor

def generate_realistic_email(prefix, index):
    """Generate realistic email addresses"""
    domains = ["example.com", "demo.org", "test.net", "sample.io", "demoapp.com"]
    return f"{prefix}.user{index:03d}@{random.choice(domains)}"

def generate_realistic_user_id():
    """Generate realistic user ID"""
    return f"USR{random.randint(100000, 999999)}"

def insert_demo_data(connection, cursor):
    """Insert realistic demo data into all tables"""
    
    # Insert admin user
    cursor.execute("""
        INSERT OR IGNORE INTO manage_users (user, pass, type) 
        VALUES (?, ?, ?)
    """, ("admin", "admin123", "all"))
    
    # Generate realistic data for each table
    # Structure: (table_name, user_id_type)
    # user_id_type: None = no user_id, "user_id" = user_id column, "source_user_id" = source_user_id column, "both" = both source and target user_ids
    tables = [
        ("user_subscriptions", None),
        ("account_migrations", None),
        ("subscription_mappings", "user_id"),
        ("dual_subscription_mappings", "both")
    ]
    
    first_names = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Jessica", "William", "Ashley"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    for table_name, user_id_type in tables:
        for i in range(15):  # 15 records per table
            # Generate realistic email addresses
            source_first = random.choice(first_names)
            target_first = random.choice(first_names)
            source = generate_realistic_email(source_first.lower(), i)
            target = generate_realistic_email(target_first.lower(), i + 100)
            
            # Create mix of expired and active subscriptions
            # 40% expired, 60% active
            if i < 6:  # First 6 records are expired
                # Expired: from_date is 60-180 days ago, to_date is 1-30 days ago
                days_ago_start = random.randint(60, 180)
                from_date = (datetime.now() - timedelta(days=days_ago_start)).strftime('%Y-%m-%d')
                days_ago_end = random.randint(1, 30)
                to_date = (datetime.now() - timedelta(days=days_ago_end)).strftime('%Y-%m-%d')
                period = (datetime.strptime(to_date, '%Y-%m-%d') - datetime.strptime(from_date, '%Y-%m-%d')).days
                creation_timestamp = (datetime.now() - timedelta(days=days_ago_start)).strftime('%Y-%m-%d %I:%M:%S %p')
            else:  # Remaining records are active
                # Active: from_date is 0-90 days ago, to_date is in the future
                period = random.randint(30, 365)
                days_ago_start = random.randint(0, 90)
                from_date = (datetime.now() - timedelta(days=days_ago_start)).strftime('%Y-%m-%d')
                days_future = random.randint(1, period)
                to_date = (datetime.now() + timedelta(days=days_future)).strftime('%Y-%m-%d')
                creation_timestamp = (datetime.now() - timedelta(days=days_ago_start)).strftime('%Y-%m-%d %I:%M:%S %p')
            
            # Generate update_date (all records have been updated at some point)
            # Update date is between creation date and now
            update_datetime = datetime.strptime(creation_timestamp, '%Y-%m-%d %I:%M:%S %p') + timedelta(
                days=random.randint(1, min(10, period // 30)),  # Update within reasonable time
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            # Make sure update_date doesn't exceed current time
            if update_datetime > datetime.now():
                update_datetime = datetime.now() - timedelta(hours=random.randint(1, 24))
            update_date = update_datetime.strftime('%Y-%m-%d %I:%M:%S %p')
            updated_by = random.choice(["admin", "manager", "operator"])
            
            # Generate last_login (all users have login history)
            login_datetime = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            last_login = login_datetime.strftime('%Y-%m-%d %I:%M:%S %p')
            
            added_by = random.choice(["admin", "manager", "operator"])
            balance = round(random.uniform(100.0, 10000.0), 2)
            
            if user_id_type == "both":
                # dual_subscription_mappings
                source_user_id = generate_realistic_user_id()
                target_user_id = generate_realistic_user_id()
                source_balance = round(random.uniform(100.0, 10000.0), 2)
                target_balance = round(random.uniform(100.0, 10000.0), 2)
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    (source_account, target_account, period, from_date, to_date, date, update_date,
                     source_user_id, target_user_id, last_login, added_by, updated_by, 
                     source_balance, target_balance) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (source, target, period, from_date, to_date, creation_timestamp, update_date,
                      source_user_id, target_user_id, last_login, added_by, updated_by,
                      source_balance, target_balance))
            elif user_id_type == "user_id":
                # subscription_mappings
                user_id = generate_realistic_user_id()
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    (source_account, target_account, period, from_date, to_date, date, update_date,
                     user_id, last_login, added_by, updated_by, balance) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (source, target, period, from_date, to_date, creation_timestamp, update_date,
                      user_id, last_login, added_by, updated_by, balance))
            else:
                # user_subscriptions, account_migrations
                cursor.execute(f"""
                    INSERT INTO {table_name} 
                    (source_account, target_account, period, from_date, to_date, date, update_date,
                     last_login, added_by, updated_by, balance) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (source, target, period, from_date, to_date, creation_timestamp, update_date,
                      last_login, added_by, updated_by, balance))
    
    connection.commit()
    print(f"Demo database '{DB_NAME}' created successfully with realistic sample data!")

if __name__ == "__main__":
    connection, cursor = create_database()
    insert_demo_data(connection, cursor)
    connection.close()
