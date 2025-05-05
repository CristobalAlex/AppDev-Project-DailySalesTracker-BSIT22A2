from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel
from PyQt6 import uic
from controls.account_window import AccountWindow
from main import LoginWindow 
from db.db_functions import Database
from controls.add_product import ProductMainWindow
from controls.order import MakeOrderWindow
from controls.sales_history import SalesHistoryWindow
from PyQt6.QtCore import QDateTime, QTimer #added sa time ng dashboard

class DashboardWindow(QMainWindow):
    def __init__(self, user_data, db_config, parent=None):
        super().__init__(parent)
        uic.loadUi("ui/dashboard.ui", self)
        self.setWindowTitle("Dashboard")

        self.db_config = db_config
        self.user_data = user_data
        self.is_logged_in = False
        self.account_window = None
        self.login_window = None

        #buttonsconnections
        self.productBtn.clicked.connect(self.check_login_for_products)
        self.makeorderBtn.clicked.connect(self.check_login_for_makeorder)
        self.salesreportBtn.clicked.connect(self.check_login_for_salesreport)
        #sa combobox handling
        self.choices.currentTextChanged.connect(self.handle_choice_change)

        #datetimer
        self.dateTimeLabel = self.findChild(QLabel, "dateTimeLabel")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()

    def update_date_time(self):
        current_datetime = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")   
        self.dateTimeLabel.setText(f"Date & Time: {current_datetime}")
        
    def handle_choice_change(self, choice):
        if choice == "Dashboard":
            self.set_buttons_visible(True)
        elif choice == "Account":
            self.set_buttons_visible(False)
            self.check_login_for_account()

    def set_buttons_visible(self, visible):
        self.productBtn.setVisible(visible)
        self.makeorderBtn.setVisible(visible)
        self.salesreportBtn.setVisible(visible)
    
    def open_products_section(self):
        #open yung products
        self.add_product = ProductMainWindow(
            user_id=self.user_data["userId"],
            db_config=self.db_config,
            dashboard_callback=self.show_dashboard_again
        )
        self.add_product.show()
        self.close()
        
    def open_make_order_section(self):
        #open yung make order
        self.make_order_window = MakeOrderWindow(
        user_id=self.user_data["userId"],
        db_config=self.db_config,
        dashboard_window=self
    )

        self.make_order_window.show()
        self.close()
        
    def open_sales_report_section(self):
        #open yunng sales report
        self.sales_report_window = SalesHistoryWindow(
            user_id=self.user_data["userId"],
            db_config=self.db_config,
            dashboard_window=self
        )
        self.sales_report_window.show()
        self.close()
    def check_login_for_account(self):
        if self.is_logged_in:
            self.redirect_to_account()
        else:
            self.show_login_prompt("Account")

    def check_login_for_products(self):
        if self.is_logged_in:
            self.open_products_section()
        else:
            self.show_login_prompt("Products")

    def check_login_for_makeorder(self):
        if self.is_logged_in:
            self.open_make_order_section()
        else:
            self.show_login_prompt("Make Order")

    def check_login_for_salesreport(self):
        if self.is_logged_in:
            self.open_sales_report_section()
        else:
            self.show_login_prompt("Sales Report")

    def show_login_prompt(self, section):
        msg = QMessageBox(self)
        msg.setWindowTitle("Login Required")
        msg.setText(f"You need to log in to access {section}. Would you like to log in?")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Ok).setText("Log In")

        result = msg.exec()
        if result == QMessageBox.StandardButton.Ok:
            self.open_login_window()

    def logout(self):
        self.open_login_window()
        self.close()

    def open_login_window(self):
        self.login_window = LoginWindow(Database(self.db_config))
        self.login_window.show()
        self.close()

    def on_login_success(self, user_data):
        self.user_data = user_data
        self.is_logged_in = True
        if self.login_window:
            self.login_window.close()

    def redirect_to_account(self):
        self.account_window = AccountWindow(
            self.user_data,
            self.logout,
            self.show_dashboard_again
        )
        self.account_window.show()
        self.close()
    
    def show_dashboard_again(self):
        self.new_dashboard = DashboardWindow(self.user_data, self.db_config)
        self.new_dashboard.is_logged_in = True
        self.new_dashboard.show()
