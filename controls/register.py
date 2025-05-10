import hashlib
import os
import sys
import re #used for not  accepting random charac
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QApplication, QLineEdit
from PyQt6.QtGui import QMouseEvent
from db.db_functions import Database
from db.config import db_config

class RegisterWindow(QMainWindow):
    def __init__(self, db_config):
        super().__init__()
        uic.loadUi("ui/register.ui", self)

        self.db = Database(db_config)
        self.registerBtn.clicked.connect(self.register_user)
        self.loginBtn.clicked.connect(self.open_login_window)
        self.uniqueToken.mousePressEvent = self.unique_token_clicked

    def register_user(self):
        name = self.name.text().strip()
        username = self.username.text().strip()
        password = self.password.text()
        gender = self.gender.currentText()
        unique_token = self.uniqueToken.text().strip()
        #bawal special characters or number      
        if not name or not username or not password or not unique_token:
            QMessageBox.warning(self, "Missing Info", "Please fill in all fields.")
            return
        if not re.fullmatch(r"[A-Za-z\s,]+", name):
            QMessageBox.warning(self, "Invalid Name", "Full name must only contain letters, spaces, or commas.")
            return
        try:
            existing_user = self.db.execute_query(
                "SELECT username FROM user WHERE username = ?", (username,)
            )
            if existing_user:
                QMessageBox.warning(self, "Error", "Username already exists.")
                return

            #hash password
            salt = os.urandom(16)
            encrypted_password = hashlib.pbkdf2_hmac(
                'sha256', password.encode('utf-8'), salt, 10000
            )
            password_to_store = encrypted_password.hex() + ":" + salt.hex()

            #hash unique token
            token_salt = os.urandom(16)
            encrypted_token = hashlib.pbkdf2_hmac(
                'sha256', unique_token.encode('utf-8'), token_salt, 10000
            )
            unique_token_to_store = encrypted_token.hex() + ":" + token_salt.hex()
            query = """
                INSERT INTO user (name, username, password, gender, uniqueToken)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (name, username, password_to_store, gender, unique_token_to_store)

            if self.db.execute_non_query(query, params):
                QMessageBox.information(self, "Success", "Account registered!")
                self.redirect_to_login()
            else:
                QMessageBox.critical(self, "Error", "Registration failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            self.db.disconnect()

    def open_login_window(self):
        from main import LoginWindow
        db = Database(self.db.config)
        self.login_window = LoginWindow(db)
        self.login_window.show()
        self.close()

    def redirect_to_login(self):
        self.open_login_window()

    def unique_token_clicked(self, event: QMouseEvent):
        QMessageBox.information(self, "Security Info", "This will be your authentication to change password later.")
        QLineEdit.mousePressEvent(self.uniqueToken, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegisterWindow(db_config)
    window.show()
    sys.exit(app.exec())
