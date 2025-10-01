from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QLineEdit, QLabel
from PyQt5.QtCore import Qt
from db import get_pending_ot_requests, update_ot_status

class OTAdminForm(QWidget):
    def __init__(self, admin_code):
        super().__init__()
        self.setWindowTitle("จัดการคำขอ OT (สำหรับ Admin)")
        self.resize(1000, 600)
        self.admin_code = admin_code

        layout = QVBoxLayout()

        # ตารางคำขอ
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "เหตุผล", "สถานะ"
        ])
        layout.addWidget(self.table)

        # ปุ่ม
        row_btn = QHBoxLayout()
        self.btn_approve = QPushButton("อนุมัติ")
        self.btn_reject = QPushButton("ปฏิเสธ")
        self.reject_reason = QLineEdit()
        self.reject_reason.setPlaceholderText("เหตุผลการปฏิเสธ (ถ้ามี)")

        self.btn_approve.clicked.connect(self.approve_request)
        self.btn_reject.clicked.connect(self.reject_request)

        row_btn.addWidget(self.btn_approve)
        row_btn.addWidget(self.btn_reject)
        row_btn.addWidget(QLabel("เหตุผลปฏิเสธ:"))
        row_btn.addWidget(self.reject_reason)
        layout.addLayout(row_btn)

        self.setLayout(layout)
        self.load_pending_requests()

    def load_pending_requests(self):
        rows = get_pending_ot_requests()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)

    def get_selected_request_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT ก่อน")
            return None
        return int(self.table.item(row, 0).text())

    def approve_request(self):
        request_id = self.get_selected_request_id()
        if request_id:
            update_ot_status(request_id, "Approved", self.admin_code, None)
            QMessageBox.information(self, "สำเร็จ", "อนุมัติเรียบร้อย ✅")
            self.load_pending_requests()

    def reject_request(self):
        request_id = self.get_selected_request_id()
        if request_id:
            reason = self.reject_reason.text().strip() or "ไม่ระบุ"
            update_ot_status(request_id, "Rejected", self.admin_code, reason)
            QMessageBox.information(self, "สำเร็จ", "ปฏิเสธเรียบร้อย ❌")
            self.load_pending_requests()
