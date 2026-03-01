"""
Dashboard Application
Backend management system for user accounts and subscriptions
"""

from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QSettings
from datetime import datetime
from ui_main import Ui_MainWindow
from user_manager import UserManager
from database import get_connection, close_connection, db_exists
from table_operations import fetch_table_data, populate_table_widget, add_extra_days_to_table, delete_inactive_users
from config import DB_NAME, VERSION, TABLE_WIDGET_MAP
import threading
import sys
import os


class Main(QMainWindow, Ui_MainWindow):
    """Main application window"""
    
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f'Dashboard V{VERSION}')
        self.Verion.setText(f"V{VERSION}")
        self.tabWidget.tabBar().setVisible(False)
        self.theme_name = "blue_theme.css"
        
        self.user_data = None
        self.admin = None
        self.password = None
        self.settings = QSettings('Dashboard', 'Dashboard V2.0')
        
        self.handle_buttons()
        self.save_pass_settings()
        self.setup_ui_guidance()
        self.tabWidget.setCurrentIndex(0)
        
        if not db_exists():
            self.statusBar().showMessage('Demo database not found. Run setup_demo_db.py first.', 10000)

    def handle_login(self):
        """Handle user login"""
        try:
            self.admin = self.Username.text()
            self.password = self.Password.text()

            if not self.admin or not self.password:
                self.statusBar().showMessage('Username or Password Cannot Be Empty')
                return

            conn = get_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            cursor.execute("SELECT user, pass FROM manage_users WHERE user=? AND pass=? AND type=?", 
                          (self.admin, self.password, 'all'))
            user = cursor.fetchone()
            
            if user:
                threading.Thread(target=self.fetch_all_data).start()
                
                login_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                cursor.execute('UPDATE manage_users SET last_login=? WHERE user=?', (login_time, self.admin))
                conn.commit()
                
                self.statusBar().showMessage('Successfully logged in', 20000)
                self.tabWidget.tabBar().setVisible(True)
                self.tabWidget.setCurrentIndex(1)
                self.tabWidget.tabBar().setTabVisible(0, False)
            else:
                self.statusBar().showMessage('Check Username or Password !')
            
            close_connection(conn, cursor)

        except Exception as e:
            self.statusBar().showMessage(f'Error In Login {e}')
            QMessageBox.critical(self, "Error In Login", str(e).capitalize())

    def save_pass_settings(self):
        """Load saved settings"""
        try:
            self.Username.setText(self.settings.value('admin', ''))
            
            if self.settings.value('Save_Pass_CheckBox') != "false":
                self.Password.setText(self.settings.value('Password', ''))
                self.Save_Pass_CheckBox.setChecked(True)
            
            position = self.settings.value('position')
            if position:
                self.move(position)
            
            theme = self.settings.value('theme_name')
            if theme:
                self.theme_name = theme
                self._apply_theme()

        except Exception as e:
            print(f"Error loading settings: {e}")

    def closeEvent(self, event):
        """Handle app close"""
        try:
            if self.tabWidget.currentIndex() != 0:
                conn = get_connection()
                if conn:
                    cursor = conn.cursor()
                    logout_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
                    cursor.execute("UPDATE manage_users SET last_logout=? WHERE user=? AND type=?", 
                                  (logout_time, self.admin, 'all'))
                    conn.commit()
                    close_connection(conn, cursor)
            
            self.settings.setValue('admin', self.Username.text())
            self.settings.setValue('Save_Pass_CheckBox', self.Save_Pass_CheckBox.isChecked())
            self.settings.setValue('position', self.pos())
            self.settings.setValue('theme_name', self.theme_name or "blue_theme.css")
            
            if self.Save_Pass_CheckBox.isChecked():
                self.settings.setValue('Password', self.Password.text())
        except Exception as e:
            print(f"Error in closeEvent: {e}")

    def _apply_theme(self):
        """Apply theme stylesheet"""
        if self.theme_name and os.path.exists(self.theme_name):
            with open(self.theme_name, 'r') as f:
                style = f.read()
                self.setStyleSheet("")
                self.tabWidget.setStyleSheet("")
                self.setStyleSheet(style)
                self.tabWidget.setStyleSheet(style)
                idx = 0 if self.theme_name == "blue_theme.css" else 1
                self.Search_ComboBox_9.setCurrentIndex(idx)

    def setup_ui_guidance(self):
        """Setup placeholders and tooltips"""
        button_texts = {
            "Add_Button": "Add New User",
            "Update_Button": "Update User",
            "Delete_Button": "Delete User",
            "Delete_Multi_Button": "Delete Multiple Users",
            "Search_Button": "Search User",
            "Rest_Button": "Clear Form",
            "Refresh_Button": "Refresh Table",
        }
        
        for name, text in button_texts.items():
            for i in range(1, 5):
                btn_name = name if i == 1 else f"{name}_{i}"
                btn = getattr(self, btn_name, None)
                if btn:
                    btn.setText(text)
        
        # Set placeholders
        fields = {
            "lineEdit_10": ("Enter source account email", "Source account email"),
            "lineEdit_12": ("Enter target account email", "Target account email"),
            "lineEdit_11": ("Enter period in days", "Subscription period"),
            "Search": ("Enter search term", "Search by ID, email, or both"),
        }
        
        for field_name, (placeholder, tooltip) in fields.items():
            field = getattr(self, field_name, None)
            if field:
                field.setPlaceholderText(placeholder)
                field.setToolTip(tooltip)

    def handle_buttons(self):
        """Connect button signals"""
        self.Login_Button.clicked.connect(self.handle_login)
        self.Update_Button_9.clicked.connect(self.update_theme)
        self.Add_Extra_Days_2.clicked.connect(self.add_extra_days)
        self.delete_inactive.clicked.connect(self.delete_inactive_users_function)
        
        self._connect_button_group("Add", self.add_users)
        self._connect_button_group("Refresh", self.refresh_buttons)
        self._connect_button_group("Rest", self.reset_buttons)
        self._connect_button_group("Search", self.search_buttons)
        self._connect_button_group("Delete", self.delete_buttons)
        self._connect_button_group("Delete_Multi", self.delete_multiple_buttons)
        self._connect_button_group("Update", self.update_buttons)

    def _connect_button_group(self, prefix, slot):
        """Connect buttons with similar names"""
        for i in range(1, 5):
            btn_name = f"{prefix}_Button" if i == 1 else f"{prefix}_Button_{i}"
            btn = getattr(self, btn_name, None)
            if btn:
                btn.clicked.connect(slot)

    def delete_inactive_users_function(self):
        """Delete inactive users"""
        table_name = self.Delete_Inactive_ComboBox.currentText()
        limit = int(self.limit.text()) if self.limit.text() else 0

        reply = QMessageBox.question(
            self, "Delete inactive users", 
            f"Delete inactive users from {table_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted = delete_inactive_users(table_name, limit)
            if deleted > 0:
                QMessageBox.information(self, "Users Deleted", f"Deleted {deleted} user(s)")
                self.fetch_all_data(table_name)
            else:
                QMessageBox.information(self, "No Users Deleted", "No inactive users found")

    def add_extra_days(self):
        """Add extra days to all users"""
        table_name = self.Extra_Period_ComboBox.currentText()
        days = self.Extra_Period.text()
        if days:
            if add_extra_days_to_table(table_name, days):
                self.fetch_all_data(table_name)
                self.statusBar().showMessage(f"Added {days} days to all users in {table_name}", 5000)
            else:
                QMessageBox.critical(self, "Error", "Failed to add extra days")

    def update_theme(self):
        """Update application theme"""
        self.theme_name = "dark_theme.css" if self.Search_ComboBox_9.currentIndex() == 1 else "blue_theme.css"
        self._apply_theme()

    def fetch_all_data(self, action=None, refresh=None):
        """Fetch all data from tables"""
        tables = [action] if action else list(TABLE_WIDGET_MAP.keys())
        
        threads = []
        for table_name in tables:
            widget_name = TABLE_WIDGET_MAP.get(table_name)
            if widget_name:
                widget = getattr(self, widget_name, None)
                if widget:
                    thread = threading.Thread(target=self._fetch_table, args=(table_name, widget))
                    thread.start()
                    threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        if refresh:
            self.statusBar().showMessage("Refresh Finished!", 20000)

    def _fetch_table(self, table_name, widget):
        """Fetch and populate a single table"""
        data = fetch_table_data(table_name)
        if data:
            populate_table_widget(data, widget)

    def update_buttons(self):
        """Handle update button clicks"""
        mapping = {
            "Update_Button": ("user_subscriptions", ("lineEdit_10", "lineEdit_12", "lineEdit_11"), "source_account", "target_account"),
            "Update_Button_2": ("account_migrations", ("lineEdit_14", "lineEdit_16", "lineEdit_19"), "source_account", "target_account"),
            "Update_Button_3": ("subscription_mappings", ("Master", "Client", "Period", "user_id"), "source_account", "target_account", "user_id"),
            "Update_Button_4": ("dual_subscription_mappings", ("Master_4", "master_user_id_7", "Client_4", "client_user_id_7", "Period_4"), 
                               "source_account", "target_account", "source_user_id", "target_user_id")
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            table, inputs, *args = mapping[btn]
            self._update_user(table, inputs, args)

    def _update_user(self, table_name, inputs, additional_args):
        """Update user in database"""
        if not self.user_data:
            QMessageBox.information(self, "No User Selected", "Please search for a user first")
            return
        
        user_id, user_table, from_date = self.user_data[0]
        if user_table != table_name:
            QMessageBox.warning(self, "Table Mismatch", "Selected user is from a different table")
            return
        
        data = [getattr(self, inp).text() for inp in inputs]
        if not all(data):
            QMessageBox.information(self, "Empty Data!", "Please fill all fields")
            return
        
        result = UserManager.update_user(table_name, user_id, from_date, data, additional_args)
        if result['success']:
            self.fetch_all_data(table_name)
            self.statusBar().showMessage(result['message'], 5000)
        else:
            QMessageBox.critical(self, "Error", result['message'])

    def delete_buttons(self):
        """Handle delete button clicks"""
        mapping = {
            "Delete_Button": ("user_subscriptions", ("Search", "lineEdit_10", "lineEdit_12", "lineEdit_11")),
            "Delete_Button_2": ("account_migrations", ("Search_2", "lineEdit_14", "lineEdit_16", "lineEdit_19")),
            "Delete_Button_3": ("subscription_mappings", ("Search_3", "Master", "Client", "Period", "user_id")),
            "Delete_Button_4": ("dual_subscription_mappings", ("Search_4", "Master_4", "master_user_id_7", "Client_4", "client_user_id_7", "Period_4"))
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            table, inputs = mapping[btn]
            self._delete_user(table, inputs)

    def _delete_user(self, table_name, inputs):
        """Delete user from database"""
        if not self.user_data:
            QMessageBox.information(self, "No User Selected", "Please search for a user first")
            return
        
        user_id, user_table, _ = self.user_data[0]
        if user_table != table_name:
            QMessageBox.warning(self, "Table Mismatch", "Selected user is from a different table")
            return
        
        result = UserManager.delete_user(table_name, user_id)
        if result['success']:
            self.fetch_all_data(table_name)
            self.statusBar().showMessage(result['message'], 5000)
        else:
            QMessageBox.critical(self, "Error", result['message'])

    def delete_multiple_buttons(self):
        """Handle multiple delete"""
        mapping = {
            "Delete_Multi_Button": ("user_subscriptions", "Search"),
            "Delete_Multi_Button_2": ("account_migrations", "Search_2"),
            "Delete_Multi_Button_3": ("subscription_mappings", "Search_3"),
            "Delete_Multi_Button_4": ("dual_subscription_mappings", "Search_4")
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            table, search_field = mapping[btn]
            self._delete_multiple(table, search_field)

    def _delete_multiple(self, table_name, search_field):
        """Delete multiple users"""
        search_input = getattr(self, search_field).text()
        if not search_input:
            QMessageBox.information(self, "Empty Data!", "Enter comma-separated IDs")
            return
        
        try:
            ids = [int(x.strip()) for x in search_input.split(',')]
            result = UserManager.delete_multiple_users(table_name, ids)
            if result['success']:
                self.fetch_all_data(table_name)
                self.statusBar().showMessage(result['message'], 5000)
            else:
                QMessageBox.critical(self, "Error", result['message'])
        except ValueError:
            QMessageBox.critical(self, "Invalid Format", "IDs must be integers separated by commas")

    def search_buttons(self):
        """Handle search button clicks"""
        mapping = {
            "Search_Button": ("user_subscriptions", "tableWidget", ("Search", "Search_ComboBox", "lineEdit_10", "lineEdit_12", "lineEdit_11")),
            "Search_Button_2": ("account_migrations", "tableWidget_2", ("Search_2", "Search_ComboBox_2", "lineEdit_14", "lineEdit_16", "lineEdit_19"), None, "target_account"),
            "Search_Button_3": ("subscription_mappings", "tableWidget_3", ("Search_3", "Search_ComboBox_3", "Master", "Client", "Period", "user_id"), None, "target_account"),
            "Search_Button_4": ("dual_subscription_mappings", "tableWidget_4", ("Search_4", "Search_ComboBox_4", "Master_4", "master_user_id_7", "Client_4", "client_user_id_7", "Period_4"), "source_account", "target_account")
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            table, widget, inputs, *args = mapping[btn]
            self._search_users(table, widget, inputs, *args)

    def _search_users(self, table_name, widget_name, inputs, source=None, target=None):
        """Search for users"""
        search_field, combo_field, *form_fields = inputs
        combo = getattr(self, combo_field)
        
        if combo.currentIndex() == 0:
            self.statusBar().showMessage("Please select a search type", 3000)
            return
        
        user_input = getattr(self, search_field).text()
        if not user_input:
            QMessageBox.information(self, "Empty Search", "Please enter a search term")
            return
        
        search_type = combo.currentIndex()
        source = source or "source_account"
        target = target or "target_account"
        
        try:
            if search_type == 1:
                user_input = int(user_input)
            elif search_type == 4 and ',' not in str(user_input):
                QMessageBox.information(self, "Invalid Format", "Use: email1, email2")
                return
        except ValueError:
            QMessageBox.critical(self, "Invalid ID", "ID must be a number")
            return
        
        result = UserManager.search_users(table_name, search_type, user_input, source, target)
        
        if result['success'] and result['data']:
            data = result['data']
            
            # Get from_date index
            from_idx = 6 if table_name == "dual_subscription_mappings" else (5 if table_name == "subscription_mappings" else 4)
            self.user_data = [(row[0], table_name, row[from_idx]) for row in data]
            
            # Populate form
            first_row = data[0]
            for field, value in zip(form_fields, first_row[1:]):
                widget = getattr(self, field, None)
                if widget:
                    widget.setText(str(value))
            
            # Show in table
            widget = getattr(self, widget_name)
            populate_table_widget(data, widget)
            self.statusBar().showMessage(f"Found {len(data)} record(s)", 5000)
        else:
            QMessageBox.warning(self, "No Results", "No records found")

    def reset_buttons(self):
        """Clear form fields"""
        mapping = {
            "Rest_Button": ("Search", "lineEdit_10", "lineEdit_12", "lineEdit_11"),
            "Rest_Button_2": ("Search_2", "lineEdit_14", "lineEdit_16", "lineEdit_19"),
            "Rest_Button_3": ("Search_3", "Master", "Client", "Period", "user_id"),
            "Rest_Button_4": ("Search_4", "Master_4", "Client_4", "Period_4", "master_user_id_7", "client_user_id_7")
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            for field in mapping[btn]:
                widget = getattr(self, field, None)
                if widget:
                    widget.clear()

    def add_users(self, response=None):
        """Handle add user"""
        mapping = {
            "Add_Button": ("user_subscriptions", ("lineEdit_10", "lineEdit_12", "lineEdit_11")),
            "Add_Button_2": ("account_migrations", ("lineEdit_14", "lineEdit_16", "lineEdit_19"), "", "target_account"),
            "Add_Button_3": ("subscription_mappings", ("Master", "Client", "Period"), "", "target_account", 
                           getattr(self, "user_id", None) and getattr(self, "user_id").text() or ""),
            "Add_Button_4": ("dual_subscription_mappings", ("Master_4", "Client_4", "Period_4"), "source_account", "target_account", "",
                           getattr(self, "master_user_id_7", None) and getattr(self, "master_user_id_7").text() or "",
                           getattr(self, "client_user_id_7", None) and getattr(self, "client_user_id_7").text() or "")
        }
        
        btn = self.sender().objectName()
        if btn not in mapping:
            return
        
        table, inputs, *args = mapping[btn]
        values = [getattr(self, field).text() for field in inputs]
        
        if not all(values):
            QMessageBox.information(self, "Incomplete Form", "Please fill all required fields")
            return
        
        # Validate emails
        for email in values[:2]:
            if '@' not in email or '.' not in email.split('@')[-1]:
                QMessageBox.warning(self, "Invalid Email", "Enter valid email address")
                return
        
        # Validate period
        try:
            if int(values[-1]) <= 0:
                raise ValueError
        except (ValueError, IndexError):
            QMessageBox.warning(self, "Invalid Period", "Period must be a positive number")
            return
        
        kwargs = dict(zip(["source_col_name", "target_col_name", "account_user_id", "source_user_id", "target_user_id"], args))
        user_manager = UserManager(table, "admin", *values, **kwargs)
        result = user_manager.add()
        
        if result['success']:
            self.fetch_all_data(table)
            for field in inputs:
                getattr(self, field, None) and getattr(self, field).clear()
        
        self.statusBar().showMessage(result['message'], 5000)
        if not result['success']:
            QMessageBox.warning(self, "Add Failed", result['message'])

    def refresh_buttons(self):
        """Handle refresh button"""
        mapping = {
            "Refresh_Button": "user_subscriptions",
            "Refresh_Button_2": "account_migrations",
            "Refresh_Button_3": "subscription_mappings",
            "Refresh_Button_4": "dual_subscription_mappings"
        }
        
        btn = self.sender().objectName()
        if btn in mapping:
            self.fetch_all_data(mapping[btn], refresh=True)


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    window = Main()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
