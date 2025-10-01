import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase
from db import get_connection
from main import OTForm
import os
from ot_admin import OTAdminForm
from ot_report import OTReportForm

# ✅ เพิ่ม MenuForm
class MenuForm(QWidget):
    def __init__(self, employee_code, employee_name):
        super().__init__()
        self.setWindowTitle("MENU")
        self.resize(400, 200)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"ยินดีต้อนรับ Admin: {employee_name} ({employee_code})"))

        self.btn_ot = QPushButton("จัดการคำขอ OT")
        self.btn_ot.clicked.connect(lambda: self.open_ot_admin(employee_code))
        layout.addWidget(self.btn_ot)

        self.btn_report = QPushButton("รายงานสรุป OT")
        self.btn_report.clicked.connect(self.open_ot_report) 
        layout.addWidget(self.btn_report)

        self.setLayout(layout)

    def open_ot_admin(self, admin_code):
        from ot_admin import OTAdminForm
        self.admin_window = OTAdminForm(admin_code)
        self.admin_window.show()

    def open_ot_report(self):
        self.report_window = OTReportForm()
        self.report_window.show()


class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login เข้าสู่ระบบ OT")
        self.resize(400, 200)

        layout = QVBoxLayout()

        # --- Username ---
        row_user = QHBoxLayout()
        row_user.addWidget(QLabel("Username:"))
        self.username = QLineEdit()
        self.username.setText("040243")
        row_user.addWidget(self.username)
        layout.addLayout(row_user)

        # --- Password ---
        row_pass = QHBoxLayout()
        row_pass.addWidget(QLabel("Password:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        row_pass.addWidget(self.password)
        layout.addLayout(row_pass)

        # --- Show password ---
        self.show_password = QCheckBox("แสดงรหัสผ่าน")
        self.show_password.stateChanged.connect(self.toggle_password)
        layout.addWidget(self.show_password)

        # --- Login button ---
        self.login_btn = QPushButton("เข้าสู่ระบบ")
        self.login_btn.clicked.connect(self.check_login)
        layout.addWidget(self.login_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def toggle_password(self, state):
        if state == Qt.Checked:
            self.password.setEchoMode(QLineEdit.Normal)
        else:
            self.password.setEchoMode(QLineEdit.Password)

    def check_login(self):
        user = self.username.text().strip()
        pwd = self.password.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "ผิดพลาด", "กรุณากรอก Username และ Password")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT employee_code, employee_name, department, position, employee_auth
                FROM Employee
                WHERE employee_code = ? AND employee_password = ?
            """, (user, pwd))
            row = cursor.fetchone()
            conn.close()

            if row:
                emp_code, emp_name, dept, pos, emp_auth = row
                QMessageBox.information(self, "สำเร็จ", f"ยินดีต้อนรับ {emp_name}")

                self.hide()
                if emp_auth and emp_auth.strip().lower() == "admin":
                    # ✅ เปิดหน้า MENU
                    self.menu_window = MenuForm(emp_code, emp_name)
                    self.menu_window.show()
                else:
                    # ✅ เปิดหน้า OTForm
                    self.ot_window = OTForm()
                    self.ot_window.employee_code.setText(emp_code.strip())
                    self.ot_window.employee_name.setText(emp_name.strip())
                    self.ot_window.department.setText(dept.strip())
                    self.ot_window.position.setText(pos.strip())
                    self.ot_window.load_last_requests(emp_code.strip())
                    self.ot_window.show()
            else:
                QMessageBox.critical(self, "ผิดพลาด", "Username หรือ Password ไม่ถูกต้อง ❌")

        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", f"Database error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # โหลดฟอนต์ไทย
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "THSarabun.ttf")
    font_id = QFontDatabase.addApplicationFont(font_path)

    if font_id == -1:
        print("ไม่สามารถโหลดฟอนต์ได้ ❌")
        font = QFont("Tahoma", 14)
    else:
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        font = QFont(font_families[0], 14)

    app.setFont(font)

    login = LoginForm()
    login.show()
    sys.exit(app.exec_())
