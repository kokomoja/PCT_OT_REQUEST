from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class MenuForm(QWidget):
    def __init__(self, employee_code, employee_name):
        super().__init__()
        self.setWindowTitle("MENU")
        self.resize(400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"ยินดีต้อนรับ Admin: {employee_name} ({employee_code})"))

        # ปุ่มไปหน้า OTForm
        self.btn_ot = QPushButton("จัดการคำขอ OT")
        layout.addWidget(self.btn_ot)

        # ปุ่มอื่น ๆ ในอนาคต
        self.btn_report = QPushButton("รายงานสรุป OT")
        layout.addWidget(self.btn_report)

        self.setLayout(layout)
