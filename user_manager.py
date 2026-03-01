"""
User management module
Handles user CRUD operations
"""

from datetime import datetime, timedelta
from database import get_connection, close_connection

class UserManager:
    """
    Class for managing users in the database.
    Supports multiple table structures with flexible column naming.
    """
    
    def __init__(self, table_name, admin_username, source_account_email, target_account_email, subscription_period, 
                 account_user_id=None, source_col_name=None, target_col_name=None,
                 source_user_id=None, target_user_id=None):
        """
        Initialize UserManager with user data.
        
        Args:
            table_name: Name of the table to insert into
            admin_username: Username of the admin adding the user
            source_account_email: Source account email address
            target_account_email: Target account email address
            subscription_period: Period in days
            account_user_id: Optional user ID for certain table types
            source_col_name: Column name for source account (default: 'source_account')
            target_col_name: Column name for target account (default: 'target_account')
            source_user_id: Optional source account user ID
            target_user_id: Optional target account user ID
        """
        self.table_name = table_name
        self.admin_username = admin_username
        self.source_account_email = source_account_email
        self.target_account_email = target_account_email
        self.subscription_period = subscription_period
        self.source_col_name = source_col_name or 'source_account'
        self.target_col_name = target_col_name or 'target_account'
        self.account_user_id = account_user_id
        self.source_user_id = source_user_id
        self.target_user_id = target_user_id


    def add(self):
        """Add new user to database"""
        if not all((self.source_account_email, self.target_account_email, self.subscription_period)):
            return {'success': False, 'message': 'Please add all information'}

        try:
            conn = get_connection()
            if not conn:
                return {'success': False, 'message': 'Database connection failed'}
            
            cursor = conn.cursor()
            query = f"SELECT {self.source_col_name}, {self.target_col_name} FROM {self.table_name} WHERE {self.source_col_name}=? AND {self.target_col_name}=?"
            cursor.execute(query, (self.source_account_email, self.target_account_email))
            existing = cursor.fetchone()
            
            if not existing:
                to_date = (datetime.today() + timedelta(days=int(self.subscription_period))).strftime('%Y-%m-%d')
                from_date = datetime.today().strftime('%Y-%m-%d')
                timestamp = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
                
                if self.source_user_id is not None and self.target_user_id is not None:
                    data = (self.source_account_email, self.target_account_email, self.subscription_period, 
                           timestamp, from_date, to_date, self.admin_username, self.source_user_id, self.target_user_id)
                    query = f"""INSERT INTO {self.table_name} 
                               ({self.source_col_name}, {self.target_col_name}, period, date, from_date, to_date, 
                                added_by, source_user_id, target_user_id) 
                               VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                elif self.account_user_id is not None:
                    data = (self.source_account_email, self.target_account_email, self.subscription_period, 
                           timestamp, from_date, to_date, self.admin_username, self.account_user_id)
                    query = f"""INSERT INTO {self.table_name} 
                               ({self.source_col_name}, {self.target_col_name}, period, date, from_date, to_date, 
                                added_by, user_id) 
                               VALUES(?, ?, ?, ?, ?, ?, ?, ?)"""
                else:
                    data = (self.source_account_email, self.target_account_email, self.subscription_period, 
                           timestamp, from_date, to_date, self.admin_username)
                    query = f"""INSERT INTO {self.table_name} 
                               ({self.source_col_name}, {self.target_col_name}, period, date, from_date, to_date, added_by) 
                               VALUES(?, ?, ?, ?, ?, ?, ?)"""
                
                cursor.execute(query, data)
                conn.commit()
                close_connection(conn, cursor)
                return {'success': True, 'message': f'User added successfully to {self.table_name}'}
            else:
                close_connection(conn, cursor)
                return {'success': False, 'message': 'User already exists'}

        except Exception as e:
            return {'success': False, 'message': f'Error in adding user: {str(e)}'}

    @staticmethod
    def update_user(table_name, user_id, from_date_string, data_to_update, additional_args):
        """Update user in database"""
        try:
            id_name = None
            source_user_id = None
            target_user_id = None
            
            if len(additional_args) == 4:
                source, source_user_id, target, target_user_id = additional_args
            elif len(additional_args) == 3:
                source, target, id_name = additional_args
            else:
                source, target = additional_args

            # Build query based on table structure
            if table_name == "dual_subscription_mappings":
                # Inputs: Master_4, master_user_id_7, Client_4, client_user_id_7, Period_4
                # Maps to: source_account, source_user_id, target_account, target_user_id, period
                # Query needs: source, target, source_user_id, target_user_id, period
                period = data_to_update[4]
            elif table_name == "subscription_mappings":
                period = data_to_update[2]
            else:
                period = data_to_update[2]

            to_date = datetime.strptime(from_date_string, '%Y-%m-%d') + timedelta(days=int(period))
            to_date = datetime.strftime(to_date, '%Y-%m-%d')
            update_date = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            admin = "admin"
            
            conn = get_connection()
            if not conn:
                return {'success': False, 'message': 'Database connection failed'}
            
            cursor = conn.cursor()
            
            try:
                if table_name == "dual_subscription_mappings":
                    query = f"UPDATE {table_name} SET {source}=?, {target}=?, {source_user_id}=?, {target_user_id}=?, period=?, to_date=?, update_date=?, updated_by=? WHERE id=?"
                    cursor.execute(query, (data_to_update[0], data_to_update[2], data_to_update[1], data_to_update[3], period, to_date, update_date, admin, user_id))
                elif table_name == "subscription_mappings":
                    query = f"UPDATE {table_name} SET {source}=?, {target}=?, period=?, {id_name}=?, to_date=?, update_date=?, updated_by=? WHERE id=?"
                    cursor.execute(query, (data_to_update[0], data_to_update[1], period, data_to_update[3], to_date, update_date, admin, user_id))
                else:
                    query = f"UPDATE {table_name} SET {source}=?, {target}=?, period=?, to_date=?, update_date=?, updated_by=? WHERE id=?"
                    cursor.execute(query, (data_to_update[0], data_to_update[1], period, to_date, update_date, admin, user_id))
                
                conn.commit()
                close_connection(conn, cursor)
                return {'success': True, 'message': 'User updated successfully!'}
            except Exception as e:
                close_connection(conn, cursor)
                return {'success': False, 'message': f'Error updating user: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'Error in update function: {str(e)}'}

    @staticmethod
    def delete_user(table_name, user_id):
        """Delete single user from database"""
        try:
            conn = get_connection()
            if not conn:
                return {'success': False, 'message': 'Database connection failed', 'rows_deleted': 0}
            
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (user_id,))
            rows_deleted = cursor.rowcount
            conn.commit()
            close_connection(conn, cursor)
            return {'success': True, 'message': f'User deleted successfully! (ID: {user_id})', 'rows_deleted': rows_deleted}
        except Exception as e:
            return {'success': False, 'message': f'Error deleting user: {str(e)}', 'rows_deleted': 0}

    @staticmethod
    def delete_multiple_users(table_name, id_list):
        """Delete multiple users from database"""
        try:
            conn = get_connection()
            if not conn:
                return {'success': False, 'message': 'Database connection failed', 'rows_deleted': 0}
            
            cursor = conn.cursor()
            rows_deleted = 0
            for id_value in id_list:
                cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (id_value,))
                rows_deleted += cursor.rowcount
            conn.commit()
            close_connection(conn, cursor)
            return {'success': True, 'message': f'{rows_deleted} user(s) deleted successfully!', 'rows_deleted': rows_deleted}
        except Exception as e:
            return {'success': False, 'message': f'Error deleting users: {str(e)}', 'rows_deleted': 0}

    @staticmethod
    def search_users(table_name, search_type, user_input, source_col="source_account", target_col="target_account"):
        """Search for users in database"""
        try:
            # Define column order for each table to match UI expectations
            column_orders = {
                "user_subscriptions": "id, source_account, target_account, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
                "account_migrations": "id, source_account, target_account, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
                "subscription_mappings": "id, source_account, target_account, period, user_id, from_date, to_date, date, update_date, last_login, added_by, updated_by, balance",
                "dual_subscription_mappings": "id, source_account, source_user_id, target_account, target_user_id, period, from_date, to_date, date, update_date, last_login, added_by, updated_by, source_balance, target_balance"
            }
            
            # Get column order for this table
            column_order = column_orders.get(table_name, "*")
            if column_order != "*":
                column_order = f"SELECT {column_order} FROM {table_name}"
            else:
                column_order = f"SELECT * FROM {table_name}"
            
            query_format = {
                1: f"{column_order} WHERE id=?",
                2: f"{column_order} WHERE {source_col}=?",
                3: f"{column_order} WHERE {target_col}=?",
                4: f"{column_order} WHERE {source_col}=? AND {target_col}=?"
            }

            query = query_format.get(search_type)
            if not query:
                return {'success': False, 'data': [], 'message': 'Invalid search type'}

            conn = get_connection()
            if not conn:
                return {'success': False, 'data': [], 'message': 'Database connection failed'}
            
            cursor = conn.cursor()
            
            if search_type == 4:
                if isinstance(user_input, str) and ',' in user_input:
                    source_val, target_val = user_input.split(',')
                    cursor.execute(query, (source_val.strip(), target_val.strip()))
                else:
                    close_connection(conn, cursor)
                    return {'success': False, 'data': [], 'message': 'For Source & Target search, use format: email1, email2'}
            elif search_type == 1:
                cursor.execute(query, (user_input,))
            else:
                cursor.execute(query, (str(user_input),))

            all_data = cursor.fetchall()
            close_connection(conn, cursor)
            
            if all_data:
                return {'success': True, 'data': all_data, 'message': f'Found {len(all_data)} record(s)'}
            else:
                return {'success': False, 'data': [], 'message': 'No records found'}
                
        except Exception as e:
            return {'success': False, 'data': [], 'message': f'Error searching: {str(e)}'}
