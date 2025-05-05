import hashlib
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLineEdit, QApplication
from controls.register import RegisterWindow
from db.db_functions import Database
from db.config import db_config

class LoginWindow(QMainWindow):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/login.ui", self)
        self.db = db
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.loginBtn.clicked.connect(self.login_user)
        self.showPasswordCheck.stateChanged.connect(self.toggle_password_visibility)
        self.registerBtn.clicked.connect(self.open_register_window)

    def login_user(self):
        username = self.username.text()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(self, "Missing Info", "Please enter both username and password.")
            return
        try:
            self.db.connect()
            user = self.db.execute_query("SELECT userId, name, username, password, gender, accountDateCreated, uniqueToken FROM user WHERE username = %s", (username,))            
            if not user:
                QMessageBox.warning(self, "Error", f"Account '{username}' isn't registered.")
                return
            db_password = user[0]["password"]
            
            if ':' not in db_password:
                QMessageBox.critical(self, "Error", "Invalid credentials. Please try again.")
                return
            encrypted_stored, salt_hex = db_password.split(":")
            salt = bytes.fromhex(salt_hex)
            encrypted_input = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000).hex()

            #password verification
            if encrypted_input == encrypted_stored:
                from controls.dashboard_window import DashboardWindow
                user_data = {
                    "userId": user[0]["userId"],
                    "name": user[0]["name"],
                    "username": user[0]["username"],
                    "password": user[0]["password"],
                    "gender": user[0].get("gender", "N/A"),
                    "accountDateCreated": user[0].get("accountDateCreated", "N/A"),
                    "uniqueToken":user[0].get("uniqueToken", "N/A")
                }

                self.dashboard = DashboardWindow(user_data, self.db.config)
                self.dashboard.on_login_success(user_data)
                self.dashboard.show()
                self.close()

            else:
                QMessageBox.warning(self, "Error", "Invalid credentials. Please try again.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def show_dashboard(self, user_data):
        from controls.dashboard_window import DashboardWindow
        user_data= {
            "userId": user_data.get("userId", "N/A"),
            "name": user_data["name"],
            "username": user_data["username"],
            "password": user_data["password"],
            "gender": user_data.get("gender", "Not Specified"),
            "accountDateCreated": user_data.get("accountDateCreated", "N/A"),
            "uniqueToken":user_data.get("uniqueToken", "N/A")
        }
        self.dashboard = DashboardWindow(user_data)
        self.dashboard.show()
        self.close()

    def toggle_password_visibility(self):
        mode = QLineEdit.EchoMode.Normal if self.showPasswordCheck.isChecked() else QLineEdit.EchoMode.Password
        self.password.setEchoMode(mode)

    def open_register_window(self):
        self.register_window = RegisterWindow(db_config)
        self.register_window.show()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    from db.db_functions import Database
    app = QApplication(sys.argv)
    db = Database(db_config)
    window = LoginWindow(db)
    window.show()
    sys.exit(app.exec())
