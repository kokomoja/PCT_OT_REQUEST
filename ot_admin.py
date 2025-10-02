from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QLineEdit, QLabel, QCheckBox
)
from PyQt5.QtCore import Qt
from db import get_pending_ot_requests, update_ot_status, update_ot_time

class OTAdminForm(QWidget):
    def __init__(self, admin_code):
        super().__init__()
        self.setWindowTitle("จัดการคำขอ OT (สำหรับ Admin)")
        self.resize(1350, 600)
        self.admin_code = admin_code

        layout = QVBoxLayout()

        # ตารางคำขอ
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "เลือก", "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "เหตุผล", "รายละเอียดงาน",
            "สถานะ", "Status (สี)"
        ])
        self.table.setColumnWidth(0, 40)   # checkbox
        self.table.setColumnWidth(9, 200)  # ot_reason
        self.table.setColumnWidth(10, 250) # job_description
        layout.addWidget(self.table)

        # ปุ่ม
        row_btn = QHBoxLayout()
        self.btn_approve = QPushButton("อนุมัติที่เลือก")
        self.btn_reject = QPushButton("ปฏิเสธที่เลือก")
        self.btn_update_time = QPushButton("บันทึกเวลาที่แก้ไข")  # ✅ ปุ่มใหม่
        self.reject_reason = QLineEdit()
        self.reject_reason.setPlaceholderText("เหตุผลการปฏิเสธ (ถ้ามี)")

        self.btn_approve.clicked.connect(self.approve_request)
        self.btn_reject.clicked.connect(self.reject_request)
        self.btn_update_time.clicked.connect(self.update_time_request)  # ✅ เชื่อม event

        row_btn.addWidget(self.btn_approve)
        row_btn.addWidget(self.btn_reject)
        row_btn.addWidget(self.btn_update_time)
        row_btn.addWidget(QLabel("เหตุผลปฏิเสธ:"))
        row_btn.addWidget(self.reject_reason)
        layout.addLayout(row_btn)

        self.setLayout(layout)
        self.load_pending_requests()

    def load_pending_requests(self):
        rows = get_pending_ot_requests()
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:10px;")
            self.table.setCellWidget(i, 0, checkbox)

            # วนใส่ข้อมูล (ยกเว้น status)
            for j, value in enumerate(row[:-1]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)

                # ✅ ทำให้คอลัมน์เวลา (Start, End) แก้ไขได้
                if j in [6, 7]:  # start_time, end_time
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                self.table.setItem(i, j + 1, item)

            # ✅ สถานะปกติ
            status_value = row[-1]
            item_status = QTableWidgetItem(str(status_value))
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 11, item_status)

            # ✅ สถานะแบบสี
            item_status_color = QTableWidgetItem(str(status_value))
            item_status_color.setTextAlignment(Qt.AlignCenter)
            if status_value == "Approved":
                item_status_color.setBackground(Qt.green)
                item_status_color.setForeground(Qt.white)
            elif status_value == "Rejected":
                item_status_color.setBackground(Qt.red)
                item_status_color.setForeground(Qt.white)
            else:
                item_status_color.setBackground(Qt.yellow)
                item_status_color.setForeground(Qt.black)
            item_status_color.setFlags(item_status_color.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 12, item_status_color)

    def get_selected_request_ids(self):
        selected_ids = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                req_id = int(self.table.item(i, 1).text())
                selected_ids.append((i, req_id))  # เก็บ row index ด้วย
        return selected_ids

    def approve_request(self):
        request_ids = [req_id for _, req_id in self.get_selected_request_ids()]
        if not request_ids:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT อย่างน้อย 1 รายการ")
            return
        for req_id in request_ids:
            update_ot_status(req_id, "Approved", self.admin_code, None)
        QMessageBox.information(self, "สำเร็จ", f"อนุมัติ {len(request_ids)} รายการเรียบร้อย ✅")
        self.load_pending_requests()

    def reject_request(self):
        request_ids = [req_id for _, req_id in self.get_selected_request_ids()]
        if not request_ids:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT อย่างน้อย 1 รายการ")
            return
        reason = self.reject_reason.text().strip() or "ไม่ระบุ"
        for req_id in request_ids:
            update_ot_status(req_id, "Rejected", self.admin_code, reason)
        QMessageBox.information(self, "สำเร็จ", f"ปฏิเสธ {len(request_ids)} รายการเรียบร้อย ❌")
        self.load_pending_requests()

    def update_time_request(self):
        selected = self.get_selected_request_ids()
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT ที่ต้องการแก้ไขเวลา")
            return

        for row_idx, req_id in selected:
            start_time = self.table.item(row_idx, 7).text()
            end_time = self.table.item(row_idx, 8).text()
            update_ot_time(req_id, start_time, end_time)

        QMessageBox.information(self, "สำเร็จ", f"อัปเดตเวลา {len(selected)} รายการเรียบร้อย ✅")
        self.load_pending_requests()
