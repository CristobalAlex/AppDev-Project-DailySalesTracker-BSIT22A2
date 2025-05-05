from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton, QMessageBox, QCheckBox
from PyQt6 import uic
import hashlib
import os
from db.db_functions import Database
from db.config import db_config


class ChangePasswordWindow(QDialog):
    def __init__(self, user_data, back_callback):
        super().__init__()
        uic.loadUi("ui/change_password.ui", self)        
        self.setWindowTitle("Change Password")
        
        #initialize the Database object with db_config
        self.db = Database(db_config)
        # Connect to the database
        self.db.connect()

        self.user_data = user_data
        self.back_callback = back_callback
        self.verified = False

        #get widgets
        self.togglePasswordCheckbox: QCheckBox = self.findChild(QCheckBox, "togglePasswordCheckbox")
        self.uniqueToken: QLineEdit = self.findChild(QLineEdit, "uniqueToken")
        self.newPassword: QLineEdit = self.findChild(QLineEdit, "newPassword")
        self.confirmPassword: QLineEdit = self.findChild(QLineEdit, "confirmPassword")
        self.verifyBtn: QPushButton = self.findChild(QPushButton, "verifyBtn")
        self.cancelBtn: QPushButton = self.findChild(QPushButton, "cancelBtn")
        self.saveBtn: QPushButton = self.findChild(QPushButton, "saveBtn")

        #inputfields
        self.newPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.newPassword.setEnabled(False)
        self.confirmPassword.setEnabled(False)

        self.togglePasswordCheckbox.setEnabled(False)
        self.togglePasswordCheckbox.toggled.connect(self.toggle_password_visibility)

        self.saveBtn.setEnabled(False)

        #button action
        self.verifyBtn.clicked.connect(self.verify_unique_token)
        self.cancelBtn.clicked.connect(self.go_back)
        self.saveBtn.clicked.connect(self.verify_and_change_password)
        self.newPassword.textEdited.connect(self.check_verified)
        self.confirmPassword.textEdited.connect(self.check_verified)

    def verify_unique_token(self):
        self.togglePasswordCheckbox.setEnabled(True)
        token_input = self.uniqueToken.text().strip()

        try:
            username = self.user_data.get("username")
            result = self.db.execute_query(
                "SELECT uniqueToken FROM user WHERE LOWER(username) = LOWER(?)",
                (username,)
            )

            if result is None:
                QMessageBox.critical(self, "Database Error", "An error occurred during the database query.")
                return

            if len(result) == 0:
                QMessageBox.critical(self, "Error", "User not found or no token set.")
                return

            stored_token = result[0]["uniqueToken"]

            if ":" not in stored_token:
                QMessageBox.critical(self, "Error", "Stored token format is invalid.")
                return

            stored_hash, stored_salt = stored_token.split(":")
            salt_bytes = bytes.fromhex(stored_salt)

            hashed_input = hashlib.pbkdf2_hmac(
                'sha256', token_input.encode('utf-8'), salt_bytes, 10000
            ).hex()

            if hashed_input == stored_hash:
                self.verified = True
                self.newPassword.setEnabled(True)
                self.confirmPassword.setEnabled(True)
                self.saveBtn.setEnabled(True)
                QMessageBox.information(self, "Verified", "You may now enter your new password.")
            else:
                self.verified = False
                self.clear_password_fields()
                self.saveBtn.setEnabled(False)
                QMessageBox.critical(self, "Error", "Token does not match.")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            print(f"Debug: Error executing query - {e}")

    def check_verified(self):
        if not self.verified:
            QMessageBox.warning(self, "Verification Required", "Please verify your unique token first.")
            self.clear_password_fields()
            self.saveBtn.setEnabled(False)

    def verify_and_change_password(self):
        if not self.verified:
            QMessageBox.warning(self, "Verification Required", "Please verify your unique token first.")
            return

        new_password = self.newPassword.text().strip()
        confirm_password = self.confirmPassword.text().strip()

        if not new_password or not confirm_password:
            QMessageBox.warning(self, "Empty Fields", "Please fill in both password fields.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match.")
            return

        salt = os.urandom(16)
        encrypted_password = hashlib.pbkdf2_hmac('sha256', new_password.encode('utf-8'), salt, 10000)
        password_to_store = encrypted_password.hex() + ":" + salt.hex()

        try:
            success = self.db.execute_non_query(
                "UPDATE user SET password = ? WHERE username = ?",
                (password_to_store, self.user_data["username"])
            )
            if success:
                QMessageBox.information(self, "Success", "Password updated successfully.")
                self.go_back()
            else:
                QMessageBox.critical(self, "Error", "Failed to update password in the database.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating password: {str(e)}")

    def clear_password_fields(self):
        self.newPassword.clear()
        self.confirmPassword.clear()
        self.newPassword.setEnabled(False)
        self.confirmPassword.setEnabled(False)
        self.togglePasswordCheckbox.setEnabled(False)
        self.togglePasswordCheckbox.setChecked(False)

    def toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.newPassword.setEchoMode(mode)
        self.confirmPassword.setEchoMode(mode)

    def clear_fields(self):
        self.uniqueToken.clear()
        self.clear_password_fields()
        self.verified = False
        self.saveBtn.setEnabled(False)

    def go_back(self):
        self.clear_fields()
        self.close()
        self.back_callback()
