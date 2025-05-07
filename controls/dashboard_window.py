#general imports
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QLabel, QVBoxLayout, QWidget
from PyQt6 import uic
from controls.account_window import AccountWindow
from main import LoginWindow
from db.db_functions import Database
from controls.add_product import ProductMainWindow
from controls.order import MakeOrderWindow
from controls.sales_history import SalesHistoryWindow

#sa graph to lahat
from PyQt6.QtCore import QDateTime, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import calendar
import mariadb

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

        #btns
        self.productBtn.clicked.connect(self.check_login_for_products)
        self.makeorderBtn.clicked.connect(self.check_login_for_makeorder)
        self.salesreportBtn.clicked.connect(self.check_login_for_salesreport)

        #comboBox
        self.choices.currentTextChanged.connect(self.handle_choice_change)

        #dateTime
        self.dateTimeLabel = self.findChild(QLabel, "dateTimeLabel")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()

        #display bar graph
        self.load_monthly_orders_graph()
        self.load_daily_orders_graph()

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
        self.add_product = ProductMainWindow(
            user_id=self.user_data["userId"],
            db_config=self.db_config,
            dashboard_callback=self.show_dashboard_again
        )
        self.add_product.show()
        self.close()

    def open_make_order_section(self):
        self.make_order_window = MakeOrderWindow(
            user_id=self.user_data["userId"],
            db_config=self.db_config,
            dashboard_window=self,
            reload_graphs_callback=self.reload_graphs
        )
        self.make_order_window.show()
        self.close()

    def open_sales_report_section(self):
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

    def reload_graphs(self):
        self.load_monthly_orders_graph()
        self.load_daily_orders_graph()

    def clear_widget_layout(self, widget):
        old_layout = widget.layout()
        if old_layout is not None:
            while old_layout.count():
                child = old_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            QWidget().setLayout(old_layout)  # Trick to remove layout


    def update_graphs_on_new_order(self):
        self.load_monthly_orders_graph()
        self.load_daily_orders_graph()
        
    def load_monthly_orders_graph(self):
        graph_widget = self.findChild(QWidget, "monthlyOrdergraphWidget")
        self.clear_widget_layout(graph_widget)

        graph_widget.setStyleSheet("""
            QWidget {
                border-radius: 15px;
                border: 1px solid #ccc;
                background-color: #ffffff;
            }
        """)

        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MONTH(o.orderDateTime), COUNT(o.orderId)
                FROM orders o
                WHERE o.userId = ? AND YEAR(o.orderDateTime) = YEAR(CURRENT_DATE())
                GROUP BY MONTH(o.orderDateTime)
                ORDER BY MONTH(o.orderDateTime)
            """, (self.user_data["userId"],))

            results = cursor.fetchall()
            orders_by_month = {month: 0 for month in range(1, 13)}
            for month, total in results:
                orders_by_month[month] = total

            month_labels = [calendar.month_abbr[m] for m in range(1, 13)]
            totals = [orders_by_month[m] for m in range(1, 13)]
            current_year = datetime.now().year

        except Exception as e:
            print("Error loading graph:", e)
            return
        finally:
            if conn:
                cursor.close()
                conn.close()
        #inside ng graphs
        fig, ax = plt.subplots()
        bars = ax.bar(month_labels, totals, color='skyblue')
        ax.set_title("Monthly Order Totals", fontsize=10)
        ax.set_ylabel("Total Orders", fontsize=9)
        ax.set_xticks(range(len(month_labels)))
        ax.set_xticklabels(month_labels, fontsize=8)
        ax.set_yticks(range(0, max(totals) + 20, 10))
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(True, linestyle='--', alpha=0.5)

        def on_click(event):
            for i, bar in enumerate(bars):
                if bar.contains(event)[0]:
                    month_name = calendar.month_name[i + 1]
                    total = totals[i]
                    QMessageBox.information(self, "Total Orders",
                        f"Total Orders for {month_name} {current_year}: {total}")
                    break

        fig.canvas.mpl_connect("button_press_event", on_click)
        canvas = FigureCanvas(fig)
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        graph_widget.setLayout(layout)

    def load_daily_orders_graph(self):
        graph_widget = self.findChild(QWidget, "graphorderwidget")
        self.clear_widget_layout(graph_widget)

        graph_widget.setStyleSheet("""
            QWidget {
                border-radius: 15px;
                border: 1px solid #ccc;
                background-color: #ffffff;
            }
        """)

        try:
            conn = mariadb.connect(**self.db_config)
            cursor = conn.cursor()
            current_date = datetime.now()
            year = current_date.year
            month = current_date.month
            days = calendar.monthrange(year, month)[1]

            cursor.execute("""
                SELECT DAY(o.orderDateTime), COUNT(o.orderId)
                FROM orders o
                WHERE o.userId = ? AND MONTH(o.orderDateTime) = ? AND YEAR(o.orderDateTime) = ?
                GROUP BY DAY(o.orderDateTime)
                ORDER BY DAY(o.orderDateTime)
            """, (self.user_data["userId"], month, year))

            results = cursor.fetchall()
            orders_by_day = {day: 0 for day in range(1, days + 1)}
            for day, total in results:
                orders_by_day[day] = total

            day_labels = [str(d) for d in range(1, days + 1)]
            totals = [orders_by_day[d] for d in range(1, days + 1)]

        except Exception as e:
            print("Error loading daily graph:", e)
            return
        finally:
            if conn:
                cursor.close()
                conn.close()
       #inside ng graphs
        fig, ax = plt.subplots(figsize=(8, 2))
        bars = ax.bar(day_labels, totals, color='skyblue')
        ax.set_title(f"Daily Orders - {calendar.month_name[month]} {year}", fontsize=10)
        ax.set_ylabel("Total Orders", fontsize=7)
        ax.set_xlabel("Day", fontsize=6)
        ax.set_xticks(range(len(day_labels)))
        ax.set_xticklabels(day_labels, fontsize=6, rotation=45)
        max_total = max(totals) if totals else 0
        ax.set_yticks(range(0, max_total + 6, 5))
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(True, linestyle='--', alpha=0.5)

        def on_click(event):
            for i, bar in enumerate(bars):
                if bar.contains(event)[0]:
                    QMessageBox.information(self, "Total Orders",
                        f"Total Orders for {calendar.month_name[month]} {i + 1}, {year}: {totals[i]}")
                    break

        fig.canvas.mpl_connect("button_press_event", on_click)
        fig.tight_layout()
        canvas = FigureCanvas(fig)
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        graph_widget.setLayout(layout)
