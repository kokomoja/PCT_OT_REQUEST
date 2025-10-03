from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from ot_admin import OTAdminForm
from ot_report import OTReportForm
from utils import confirm_dialog

class MenuForm(QWidget):
    def __init__(self, employee_code, employee_name, department, position, login_window):
        super().__init__()
        self.setWindowTitle("MENU")
        self.resize(400, 300)

        # เก็บ reference หน้า Login
        self.login_window = login_window

        # ✅ เก็บหน้าต่างที่เปิดอยู่ทั้งหมด
        self.open_windows = []

        layout = QVBoxLayout()

        # ข้อมูลพนักงาน
        layout.addWidget(QLabel(f"ยินดีต้อนรับ Admin: {employee_name} ({employee_code})"))
        layout.addWidget(QLabel(f"แผนก: {department}"))
        layout.addWidget(QLabel(f"ตำแหน่ง: {position}"))

        # ปุ่มไปหน้า OT Admin
        self.btn_ot = QPushButton("จัดการคำขอ OT")
        self.btn_ot.clicked.connect(lambda: self.open_ot_admin(employee_code))
        layout.addWidget(self.btn_ot)

        # ปุ่มไปหน้า Report
        self.btn_report = QPushButton("รายงานสรุป OT")
        self.btn_report.clicked.connect(self.open_ot_report)
        layout.addWidget(self.btn_report)

        # ปุ่ม Logout
        self.btn_logout = QPushButton("ออกจากระบบ")
        self.btn_logout.clicked.connect(self.logout)
        layout.addWidget(self.btn_logout)

        self.setLayout(layout)

    def open_ot_admin(self, admin_code):
        admin_window = OTAdminForm(admin_code)
        admin_window.show()
        self.open_windows.append(admin_window)  # ✅ เก็บ reference

    def open_ot_report(self):
        report_window = OTReportForm()
        report_window.show()
        self.open_windows.append(report_window)  # ✅ เก็บ reference

    def logout(self):
        # ✅ Popup ยืนยัน (ใช้ util กลาง)
        if not confirm_dialog(self, "ยืนยันการออกจากระบบ", "คุณแน่ใจหรือไม่ว่าต้องการออกจากระบบ?"):
            return

        # ปิดทุกหน้าต่างที่เปิด
        for win in self.open_windows:
            try:
                win.close()
            except Exception:
                pass
        self.open_windows.clear()

        # ปิดหน้าเมนู
        self.close()

        # เคลียร์ login form
        self.login_window.clear_fields()
        self.login_window.show()
