"""
Table operations module
Handles CRUD operations for database tables
"""

from datetime import datetime, timedelta
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from database import get_connection, close_connection


# Column order mapping for each table
COLUMN_ORDERS = {
    "user_subscriptions": "id, source_account, target_account, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
    "account_migrations": "id, source_account, target_account, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
    "subscription_mappings": "id, source_account, target_account, period, user_id, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
    "dual_subscription_mappings": "id, source_account, source_user_id, target_account, target_user_id, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, source_balance, target_balance"
}


def fetch_table_data(table_name, extra_days=None):
    """Fetch all data from a table"""
    conn = get_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    if table_name in COLUMN_ORDERS:
        query = f"SELECT {COLUMN_ORDERS[table_name]} FROM {table_name}"
    else:
        query = f"SELECT * FROM {table_name}"
    
    cursor.execute(query)
    data = cursor.fetchall()
    close_connection(conn, cursor)
    
    return data


def populate_table_widget(data, table_widget):
    """Populate table widget with data and auto-resize columns"""
    table_widget.clearContents()
    table_widget.setRowCount(len(data))
    table_widget.setEditTriggers(table_widget.NoEditTriggers)
    
    font_metrics = table_widget.fontMetrics()
    max_widths = {}
    
    # Check header widths
    for col_idx in range(table_widget.columnCount()):
        header = table_widget.horizontalHeaderItem(col_idx)
        if header:
            max_widths[col_idx] = font_metrics.width(header.text())
    
    # Populate data and calculate widths
    for row_idx, row in enumerate(data):
        for col_idx, value in enumerate(row):
            text = str(value) if value is not None else ""
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table_widget.setItem(row_idx, col_idx, item)
            
            text_width = font_metrics.width(text) + 20
            if col_idx not in max_widths or text_width > max_widths[col_idx]:
                max_widths[col_idx] = text_width
    
    # Resize columns
    for col_idx, width in max_widths.items():
        table_widget.setColumnWidth(col_idx, min(width, 300))


def add_extra_days_to_table(table_name, days_to_add):
    """Add extra days to all users in a table"""
    try:
        update_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, period, to_date FROM {table_name}")
        records = cursor.fetchall()
        
        for record in records:
            new_period = int(days_to_add) + record[1]
            new_to_date = datetime.strptime(record[2], '%Y-%m-%d') + timedelta(days=int(days_to_add))
            new_to_date = new_to_date.strftime('%Y-%m-%d')
            
            cursor.execute(
                f"UPDATE {table_name} SET period=?, to_date=?, update_date=?, updated_by=? WHERE id=?",
                (new_period, new_to_date, update_time, "admin", record[0])
            )
        
        conn.commit()
        close_connection(conn, cursor)
        return True
    except Exception as e:
        print(f"Error adding days: {e}")
        return False


def delete_inactive_users(table_name, limit):
    """Delete inactive users from a table"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        if not conn:
            return 0
        
        cursor = conn.cursor()
        
        # SQLite doesn't support parameterized LIMIT in DELETE
        # Use a subquery approach instead
        if limit and limit > 0:
            # Delete using subquery with LIMIT
            query = f"""DELETE FROM {table_name} 
                       WHERE id IN (
                           SELECT id FROM {table_name} 
                           WHERE to_date < ? 
                           LIMIT ?
                       )"""
            cursor.execute(query, (today, limit))
        else:
            # Delete all inactive users if no limit
            query = f"DELETE FROM {table_name} WHERE to_date < ?"
            cursor.execute(query, (today,))
        
        deleted = cursor.rowcount
        conn.commit()
        close_connection(conn, cursor)
        return deleted
    except Exception as e:
        print(f"Error deleting inactive users: {e}")
        return 0
