from PyQt6.QtWidgets import (
    QPushButton, QMainWindow, QApplication, QMessageBox, QLineEdit, QSpinBox
)
import mariadb
from PyQt6 import uic

class AddProductForm(QMainWindow):
    def __init__(self, user_id, db_config):
        super().__init__()
        uic.loadUi("ui/add_product_form.ui", self)
        self.user_id = user_id
        self.db_config = db_config

        self.save_btn = self.findChild(QPushButton, "saveBtn")
        self.back_btn = self.findChild(QPushButton, "backBtn")
        self.product_name_input = self.findChild(QLineEdit, "productNameInput")
        self.price_input = self.findChild(QLineEdit, "priceInput")
        self.purchase_price_input = self.findChild(QLineEdit, "purchasePriceInput")
        self.stock_input = self.findChild(QSpinBox, "stockInput")

        if self.stock_input:
            self.stock_input.setMinimum(1)

        if self.save_btn:
            self.save_btn.clicked.connect(self.save_product)
        if self.back_btn:
            self.back_btn.clicked.connect(self.go_back)

    def save_product(self):
        product_name = self.product_name_input.text()
        selling_price = self.price_input.text()
        purchase_price = self.purchase_price_input.text()
        stock = self.stock_input.value()

        if product_name and selling_price and purchase_price:
            try:
                selling_price = float(selling_price)
                purchase_price = float(purchase_price)

                conn = mariadb.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO products (productName, price, purchasePrice, stock, userId) VALUES (?, ?, ?, ?, ?)",
                    (product_name, selling_price, purchase_price, stock, self.user_id)
                )
                conn.commit()
                QMessageBox.information(self, "Success", "Product added successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                if 'conn' in locals() and conn:
                    cursor.close()
                    conn.close()
        else:
            QMessageBox.critical(self, "Error", "Please fill in all fields.")

    def go_back(self):
        self.close()
