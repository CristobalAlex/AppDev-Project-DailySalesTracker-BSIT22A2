import mariadb
import sys
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QTableWidget, QTableWidgetItem, QPushButton,
    QMessageBox, QInputDialog, QLineEdit
)
from db.config import db_config

class ShowProductsWindow(QMainWindow):
    def __init__(self, user_id, db_config):
        super().__init__()
        uic.loadUi("ui/show_products.ui", self)
        self.user_id = user_id
        self.db_config = db_config

        self.products_table = self.findChild(QTableWidget, "productsTable")
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["Product Name", "Price", "Stock", "Update Price", "Update Stock", "Remove"])

        # ✅ Search Input
        self.search_input = self.findChild(QLineEdit, "searchInput")
        if self.search_input:
            self.search_input.setClearButtonEnabled(True)
            self.search_input.textChanged.connect(self.search_products)

        self.cancel_btn = self.findChild(QPushButton, "cancelBtn")
        self.cancel_btn.clicked.connect(self.go_back)

        self.load_products()  # Load all products initially

    def search_products(self, text):
        self.load_products(text)

    def load_products(self, search_text=""):
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()

            if search_text:
                query = "SELECT productId, productName, price, stock FROM products WHERE userId = ? AND productName LIKE ?"
                cursor.execute(query, (self.user_id, f"%{search_text}%"))
            else:
                cursor.execute("SELECT productId, productName, price, stock FROM products WHERE userId = ?", (self.user_id,))

            products = cursor.fetchall()
            self.products_table.setRowCount(len(products))

            for row, product in enumerate(products):
                self.products_table.setItem(row, 0, QTableWidgetItem(product[1]))
                self.products_table.setItem(row, 1, QTableWidgetItem(str(product[2])))
                self.products_table.setItem(row, 2, QTableWidgetItem(str(product[3])))

                update_price_button = QPushButton("Update Price")
                update_price_button.clicked.connect(lambda checked, product_id=product[0]: self.update_price(product_id))
                self.products_table.setCellWidget(row, 3, update_price_button)

                update_stock_button = QPushButton("Update Stock")
                update_stock_button.clicked.connect(lambda checked, product_id=product[0]: self.update_stock(product_id))
                self.products_table.setCellWidget(row, 4, update_stock_button)

                remove_button = QPushButton("Remove")
                remove_button.clicked.connect(lambda checked, product_id=product[0]: self.remove_product(product_id))
                self.products_table.setCellWidget(row, 5, remove_button)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def update_price(self, product_id):
        price, ok = QInputDialog.getDouble(self, "Update Price", "Enter new price:")
        if ok:
            try:
                conn = mariadb.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET price = ? WHERE productId = ?", (price, product_id))
                conn.commit()
                self.load_products(self.search_input.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                if 'conn' in locals() and conn:
                    cursor.close()
                    conn.close()

    def update_stock(self, product_id):
        stock, ok = QInputDialog.getInt(self, "Update Stock", "Enter new stock:")
        if ok:
            try:
                conn = mariadb.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET stock = ? WHERE productId = ?", (stock, product_id))
                conn.commit()
                self.load_products(self.search_input.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                if 'conn' in locals() and conn:
                    cursor.close()
                    conn.close()

    def remove_product(self, product_id):
        reply = QMessageBox.question(self, "Remove Product", "Are you sure you want to remove this product?")
        if reply == QMessageBox.StandardButton.Yes:
            try:
                conn = mariadb.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE productId = ?", (product_id,))
                conn.commit()
                self.load_products(self.search_input.text())
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
            finally:
                if 'conn' in locals() and conn:
                    cursor.close()
                    conn.close()

    def go_back(self):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    user_id = 1
    window = ShowProductsWindow(user_id, db_config)
    window.show()
    sys.exit(app.exec())
