from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from ot_admin import OTAdminForm
from ot_report import OTReportForm
from utils import confirm_dialog
from employee_form import EmployeeForm

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

        # ✅ กลุ่มข้อมูลพนักงาน
        info_layout = QVBoxLayout()
        info_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # ชิดซ้ายบน
        info_layout.setSpacing(4)  # ระยะห่างระหว่างบรรทัด (px)

        label_welcome = QLabel(f"ยินดีต้อนรับ Admin: {employee_name} ({employee_code})")
        label_dept = QLabel(f"แผนก: {department}")
        label_pos = QLabel(f"ตำแหน่ง: {position}")
        
        label_welcome.setStyleSheet("font-size: 20pt; font-weight: bold;")
        label_dept.setStyleSheet("font-size: 18pt;")
        label_pos.setStyleSheet("font-size: 18pt;")

        info_layout.addWidget(label_welcome)
        info_layout.addWidget(label_dept)
        info_layout.addWidget(label_pos)

        layout.addLayout(info_layout)

        self.btn_ot = QPushButton("จัดการคำขอ OT")
        self.btn_ot.clicked.connect(lambda: self.open_ot_admin(employee_code))
        layout.addWidget(self.btn_ot)

        self.btn_report = QPushButton("รายงานสรุป OT")
        self.btn_report.clicked.connect(self.open_ot_report)
        layout.addWidget(self.btn_report)
        
        self.btn_employee = QPushButton("👨‍💼 เพิ่มรายชื่อพนักงาน")
        self.btn_employee.clicked.connect(self.open_employee_form)
        layout.addWidget(self.btn_employee)

        self.btn_logout = QPushButton("ออกจากระบบ")
        self.btn_logout.clicked.connect(self.logout)
        layout.addWidget(self.btn_logout)

        self.setLayout(layout)

    def open_ot_admin(self, admin_code):
        admin_window = OTAdminForm(admin_code)
        admin_window.show()
        self.open_windows.append(admin_window) 
        
    def open_ot_report(self):
        report_window = OTReportForm()
        report_window.show()
        self.open_windows.append(report_window)  
        
    def open_employee_form(self):
        emp_form = EmployeeForm()
        emp_form.show()
        self.open_windows.append(emp_form) 
        
    def logout(self):

        if not confirm_dialog(self, "ยืนยันการออกจากระบบ", "คุณแน่ใจหรือไม่ว่าต้องการออกจากระบบ?"):
            return

        for win in self.open_windows:
            try:
                win.close()
            except Exception:
                pass
        self.open_windows.clear()

        self.close()

        self.login_window.clear_fields()
        self.login_window.show()
