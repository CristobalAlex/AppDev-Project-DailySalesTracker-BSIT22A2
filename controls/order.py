from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLabel, QSpinBox
)
from PyQt6.QtCore import Qt
from decimal import Decimal, InvalidOperation
import mariadb
import sys
from PyQt6 import uic
from db.config import db_config

class MakeOrderWindow(QMainWindow):
    def __init__(self, user_id, db_config, dashboard_window, reload_graphs_callback):
        super().__init__()
        uic.loadUi("ui/order.ui", self)

        self.user_id = user_id
        self.db_config = db_config
        self.dashboard_window = dashboard_window
        self.low_payment_warned = False

        self.order_table = self.findChild(QTableWidget, "orderTable")
        self.total_label = self.findChild(QLabel, "totalAmountEdit")
        self.payment_edit = self.findChild(QLineEdit, "paymentEdit")
        self.change_label = self.findChild(QLabel, "changeEdit")
        self.confirm_button = self.findChild(QPushButton, "addButton")
        self.cancel_button = self.findChild(QPushButton, "cancelButton")

        self.order_table.setColumnCount(4)
        self.order_table.setHorizontalHeaderLabels(["Product Name", "Price", "Stock", "Quantity"])
        self.product_data = {}  # maps row index to product info

        self.populate_product_table()

        self.payment_edit.textChanged.connect(self.calculate_change)
        self.confirm_button.clicked.connect(self.process_order)
        self.cancel_button.clicked.connect(self.cancel_order)

        self.reload_graphs_callback = reload_graphs_callback #callback to  sa update ng orders in graphs

    def populate_product_table(self):
        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT productId, productName, price, stock FROM products WHERE userId = ?", (self.user_id,))
            products = cursor.fetchall()

            self.order_table.setRowCount(0)
            self.product_data.clear()

            for row, (product_id, name, price, stock) in enumerate(products):
                self.order_table.insertRow(row)
                self.product_data[row] = {"productId": product_id, "price": Decimal(str(price)), "stock": stock}

                for col, value in enumerate([name, f"{price:.2f}", stock]):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.order_table.setItem(row, col, item)

                spin_box = QSpinBox()
                spin_box.setRange(0, stock)
                spin_box.valueChanged.connect(self.calculate_total)
                self.order_table.setCellWidget(row, 3, spin_box)

            self.calculate_total()
        except Exception as e:
            QMessageBox.critical(self, "Error loading products", str(e))
        finally:
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def calculate_total(self):
        total = Decimal("0.00")
        for row in range(self.order_table.rowCount()):
            try:
                quantity = self.order_table.cellWidget(row, 3).value()
                price = self.product_data[row]["price"]
                total += price * quantity
            except Exception:
                continue

        self.total_label.setText(f"Total: {total:.2f}")
        self.calculate_change()

    def calculate_change(self):
        try:
            total = Decimal(self.total_label.text().replace("Total: ", ""))
            payment = Decimal(self.payment_edit.text())
            change = payment - total
            self.change_label.setText(f"Change: {change:.2f}")

            if change < 0 and not self.low_payment_warned:
                QMessageBox.warning(self, "Insufficient Payment", "Please enter enough money for this order.")
                self.low_payment_warned = True
            elif change >= 0:
                self.low_payment_warned = False
        except (InvalidOperation, ValueError):
            self.change_label.setText("")
            self.low_payment_warned = False

    def process_order(self):
        try:
            total_price = Decimal("0.00")
            order_details = []

            for row in range(self.order_table.rowCount()):
                quantity = self.order_table.cellWidget(row, 3).value()
                if quantity > 0:
                    product_info = self.product_data[row]
                    product_id = product_info["productId"]
                    price = product_info["price"]
                    total = price * quantity
                    total_price += total
                    order_details.append((product_id, quantity, total))

            if not order_details:
                QMessageBox.warning(self, "No Products Selected", "Please select at least one product.")
                return

            try:
                payment = Decimal(self.payment_edit.text())
                if payment < total_price:
                    QMessageBox.warning(self, "Insufficient Payment", "Payment must be at least equal to total.")
                    return
            except (InvalidOperation, ValueError):
                QMessageBox.warning(self, "Invalid Payment", "Please enter a valid numeric payment amount.")
                return

            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO orders (userId, totalPrice, totalMoney, changeAmount, orderDateTime)
                VALUES (?, ?, ?, ?, NOW())
            """, (
                self.user_id,
                total_price,
                payment,
                payment - total_price
            ))

            order_id = cursor.lastrowid

            for product_id, quantity, total in order_details:
                cursor.execute("""
                    INSERT INTO order_details (orderId, productId, quantity, totalPrice)
                    VALUES (?, ?, ?, ?)
                """, (order_id, product_id, quantity, total))

                cursor.execute("""
                    UPDATE products
                    SET stock = stock - ?
                    WHERE productId = ?
                """, (quantity, product_id))

            conn.commit()
            QMessageBox.information(self, "Order Success", "Order has been processed successfully.")
            self.populate_product_table()
            self.payment_edit.clear()
            self.change_label.setText("Change: 0.00")
            
            if self.reload_graphs_callback:
                self.reload_graphs_callback()    

        except Exception as e:
            QMessageBox.critical(self, "Order Error", str(e))
        finally:
            self.dashboard_window.update_graphs_on_new_order()
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def cancel_order(self):
        self.close()
        self.dashboard_window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from dashboard_window import DashboardWindow
    dashboard = DashboardWindow()
    window = MakeOrderWindow(user_id=1, db_config=db_config, dashboard_window=dashboard)
    window.show()
    sys.exit(app.exec())
