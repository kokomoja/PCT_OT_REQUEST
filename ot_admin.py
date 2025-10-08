from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QHBoxLayout, QMessageBox, QLineEdit, QLabel,
    QCheckBox, QComboBox, QDateEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, QDate, QLocale
from PyQt5.QtGui import QColor
from db import get_all_ot_requests, update_ot_status, update_ot_detail
from utils import thai_to_arabic, confirm_dialog


class OTAdminForm(QWidget):
    def __init__(self, admin_code):
        super().__init__()
        self.setWindowTitle("จัดการคำขอ OT (สำหรับ Admin)")
        self.resize(1450, 700)
        self.admin_code = admin_code

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # === Filter Row ===
        filter_row = QHBoxLayout()
        filter_row.setAlignment(Qt.AlignLeft)
        filter_row.setSpacing(15)
        filter_row.setContentsMargins(0, 0, 0, 0)

        # --- Filter: แผนก (ComboBox) ---
        lbl_dept = QLabel("แผนก:")
        self.cbb_dept = QComboBox()
        self.cbb_dept.setFixedWidth(180)
        filter_row.addWidget(lbl_dept)
        filter_row.addWidget(self.cbb_dept)

        # --- Filter: ชื่อพนักงาน (ComboBox) ---
        lbl_name = QLabel("ชื่อพนักงาน:")
        self.cbb_name = QComboBox()
        self.cbb_name.setFixedWidth(200)
        filter_row.addWidget(lbl_name)
        filter_row.addWidget(self.cbb_name)

        # --- Filter: วันที่ ---
        lbl_from = QLabel("วันที่ตั้งแต่:")
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setDisplayFormat("yyyy-MM-dd")
        self.date_from.setFixedWidth(120)

        lbl_to = QLabel("ถึง:")
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy-MM-dd")
        self.date_to.setFixedWidth(120)

        # ✅ แสดงเลขอารบิก
        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.date_from.setLocale(locale)
        self.date_to.setLocale(locale)

        filter_row.addWidget(lbl_from)
        filter_row.addWidget(self.date_from)
        filter_row.addWidget(lbl_to)
        filter_row.addWidget(self.date_to)

        # --- Filter: สถานะ ---
        lbl_status = QLabel("สถานะ:")
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["ทั้งหมด", "Pending", "Approved", "Rejected"])
        self.cmb_status.setFixedWidth(120)
        filter_row.addWidget(lbl_status)
        filter_row.addWidget(self.cmb_status)

        # --- ปุ่มเคลียร์ ---
        self.btn_clear = QPushButton("🧹 เคลียร์ตัวกรอง")
        self.btn_clear.setFixedWidth(140)
        self.btn_clear.clicked.connect(self.clear_filters)
        filter_row.addWidget(self.btn_clear)

        layout.addLayout(filter_row)

        # === Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "เลือก", "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "เหตุผล", "รายละเอียดงาน",
            "สถานะ", "สีสถานะ"
        ])
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(6, 60)
        self.table.setColumnWidth(7, 60)
        self.table.setColumnWidth(8, 60)
        self.table.setColumnWidth(9, 200)
        self.table.setColumnWidth(10, 200)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # === Buttons Row ===
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignLeft)
        btn_row.setSpacing(15)
        btn_row.setContentsMargins(0, 0, 0, 0)
        
        # --- ปุ่มต่าง ๆ ---
        self.btn_approve = QPushButton("✅ อนุมัติที่เลือก")
        self.btn_approve.setFixedSize(180, 40)
        self.btn_approve.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #43A047; }
        """)

        self.btn_reject = QPushButton("❌ ปฏิเสธที่เลือก")
        self.btn_reject.setFixedSize(180, 40)
        self.btn_reject.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)

        self.btn_update = QPushButton("💾 บันทึกการแก้ไข")
        self.btn_update.setFixedSize(200, 40)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)

        self.btn_reset = QPushButton("🔄 รีเซ็ตเป็น Pending")
        self.btn_reset.setFixedSize(200, 40)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #FB8C00; }
        """)

        # --- Label + Input ---
        lbl_reason = QLabel("เหตุผลปฏิเสธ:")
        lbl_reason.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # ✅ บังคับชิดซ้าย
        lbl_reason.setFixedWidth(110)

        self.reject_reason = QLineEdit()
        self.reject_reason.setPlaceholderText("เหตุผลปฏิเสธ (ถ้ามี)")
        self.reject_reason.setFixedSize(400, 40)
        self.reject_reason.setAlignment(Qt.AlignLeft)  # ✅ บังคับข้อความในช่องชิดซ้าย
        self.reject_reason.setStyleSheet("""
            QLineEdit {
                font-size: 16pt;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
        """)

        # --- เชื่อมปุ่มกับฟังก์ชัน ---
        self.btn_approve.clicked.connect(self.approve_request)
        self.btn_reject.clicked.connect(self.reject_request)
        self.btn_update.clicked.connect(self.update_detail_request)
        self.btn_reset.clicked.connect(self.reset_status_request)

        # --- เพิ่ม widgets เข้า layout ---
        btn_row.addWidget(self.btn_approve)
        btn_row.addWidget(self.btn_reject)
        btn_row.addWidget(self.btn_update)
        btn_row.addWidget(self.btn_reset)
        btn_row.addWidget(lbl_reason)
        btn_row.addWidget(self.reject_reason)

        # ✅ เพิ่ม stretch เล็กน้อยกันช่อง drift ไปขวา
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.setLayout(layout)

        # === Event binding สำหรับอัปเดตอัตโนมัติ ===
        self.cmb_status.currentIndexChanged.connect(self.load_requests)
        self.cbb_dept.currentIndexChanged.connect(self.load_requests)
        self.cbb_name.currentIndexChanged.connect(self.load_requests)
        self.date_from.dateChanged.connect(self.load_requests)
        self.date_to.dateChanged.connect(self.load_requests)

        # โหลดครั้งแรก
        self.load_requests()

        # Auto refresh ทุก 60 วินาที
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_requests)
        self.timer.start(60000)

    # ---------- Helper: เติมค่าตัวเลือกใน ComboBox ----------
    def populate_filter_options(self, base_rows):
        """เติม cbb_dept ด้วยแผนก และ cbb_name ด้วยชื่อพนักงาน"""
        prev_dept = self.cbb_dept.currentText() if self.cbb_dept.count() else "ทั้งหมด"
        prev_name = self.cbb_name.currentText() if self.cbb_name.count() else "ทั้งหมด"

        dept_set, name_set = set(), set()
        for r in base_rows:
            if r[3] and str(r[3]).strip():
                dept_set.add(str(r[3]).strip())
            if r[2] and str(r[2]).strip():
                name_set.add(str(r[2]).strip())

        depts = sorted(dept_set)
        names = sorted(name_set)

        self.cbb_dept.blockSignals(True)
        self.cbb_name.blockSignals(True)

        self.cbb_dept.clear()
        self.cbb_dept.addItem("ทั้งหมด")
        self.cbb_dept.addItems(depts)

        self.cbb_name.clear()
        self.cbb_name.addItem("ทั้งหมด")
        self.cbb_name.addItems(names)

        if prev_dept in depts or prev_dept == "ทั้งหมด":
            self.cbb_dept.setCurrentText(prev_dept)
        if prev_name in names or prev_name == "ทั้งหมด":
            self.cbb_name.setCurrentText(prev_name)

        self.cbb_dept.blockSignals(False)
        self.cbb_name.blockSignals(False)

    # ---------- โหลดข้อมูล ----------
    def load_requests(self):
        """โหลดคำขอ OT ตามตัวกรอง (อัปเดตอัตโนมัติ)"""
        status = self.cmb_status.currentText()
        if status == "ทั้งหมด":
            status = None

        date_from = thai_to_arabic(self.date_from.date().toString("yyyy-MM-dd"))
        date_to = thai_to_arabic(self.date_to.date().toString("yyyy-MM-dd"))

        rows = get_all_ot_requests(status)

        base_rows = []
        for row in rows:
            ot_date = thai_to_arabic(str(row[5]))  # ot_date index=5
            if date_from <= ot_date <= date_to:
                base_rows.append(row)

        # เติม combo options จากฐานข้อมูลปัจจุบัน
        self.populate_filter_options(base_rows)

        sel_dept = self.cbb_dept.currentText().strip()
        sel_name = self.cbb_name.currentText().strip()

        filtered_rows = []
        for r in base_rows:
            dept = str(r[3]).strip() if r[3] else ""
            name = str(r[2]).strip() if r[2] else ""
            if sel_dept != "ทั้งหมด" and dept != sel_dept:
                continue
            if sel_name != "ทั้งหมด" and name != sel_name:
                continue
            filtered_rows.append(r)

        # แสดงในตาราง
        self.table.setRowCount(len(filtered_rows))
        for i, row in enumerate(filtered_rows):
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:10px;")
            self.table.setCellWidget(i, 0, checkbox)

            for j, value in enumerate(row[:-1]):
                val = thai_to_arabic(str(value))
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if j in [6, 7, 8, 9]:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, j + 1, item)

            status_val = str(row[-1])
            item_status = QTableWidgetItem(status_val)
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setFlags(item_status.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 11, item_status)

            color_item = QTableWidgetItem(status_val)
            color_item.setTextAlignment(Qt.AlignCenter)
            if status_val == "Approved":
                color_item.setBackground(QColor(0, 170, 0))
                color_item.setForeground(QColor(255, 255, 255))
            elif status_val == "Rejected":
                color_item.setBackground(QColor(200, 0, 0))
                color_item.setForeground(QColor(255, 255, 255))
            else:
                color_item.setBackground(QColor(255, 235, 59))
                color_item.setForeground(QColor(0, 0, 0))
            color_item.setFlags(color_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 12, color_item)

        self.table.resizeColumnsToContents()

        # ✅ ล็อกคอลัมน์ "เลือก" ไม่ให้ปรับขนาดได้
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 30)
        
        

    # ---------- ปุ่มเคลียร์ ----------
    def clear_filters(self):
        """รีเซ็ตค่าฟิลเตอร์ทั้งหมด"""
        self.cbb_dept.blockSignals(True)
        self.cbb_name.blockSignals(True)

        self.cbb_dept.clear()
        self.cbb_name.clear()
        self.cbb_dept.addItem("ทั้งหมด")
        self.cbb_name.addItem("ทั้งหมด")
        self.cbb_dept.setCurrentIndex(0)
        self.cbb_name.setCurrentIndex(0)

        self.cmb_status.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_to.setDate(QDate.currentDate())

        self.cbb_dept.blockSignals(False)
        self.cbb_name.blockSignals(False)

        self.load_requests()

    # ---------- Helper ----------
    def get_selected_request_ids(self):
        selected = []
        for i in range(self.table.rowCount()):
            chk = self.table.cellWidget(i, 0)
            if chk and chk.isChecked():
                req_id = int(self.table.item(i, 1).text())
                selected.append((i, req_id))
        return selected

    # ---------- Actions ----------
    def approve_request(self):
        selected = self.get_selected_request_ids()
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT")
            return
        if not confirm_dialog(self, "ยืนยัน", f"ต้องการอนุมัติ {len(selected)} รายการหรือไม่?"):
            return
        for _, req_id in selected:
            update_ot_status(req_id, "Approved", self.admin_code, None)
        QMessageBox.information(self, "สำเร็จ", "อนุมัติเรียบร้อย ✅")
        self.load_requests()

    def reject_request(self):
        selected = self.get_selected_request_ids()
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT")
            return
        reason = self.reject_reason.text().strip() or "ไม่ระบุ"
        if not confirm_dialog(self, "ยืนยัน", f"ต้องการปฏิเสธ {len(selected)} รายการหรือไม่?"):
            return
        for _, req_id in selected:
            update_ot_status(req_id, "Rejected", self.admin_code, reason)
        QMessageBox.information(self, "สำเร็จ", "ปฏิเสธเรียบร้อย ❌")
        self.load_requests()

    def reset_status_request(self):
        selected = self.get_selected_request_ids()
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT ที่ต้องการรีเซ็ต")
            return
        if not confirm_dialog(self, "ยืนยัน", f"ต้องการรีเซ็ต {len(selected)} รายการกลับเป็น Pending หรือไม่?"):
            return
        for _, req_id in selected:
            update_ot_status(req_id, "Pending", self.admin_code, None)
        QMessageBox.information(self, "สำเร็จ", "รีเซ็ตสถานะเรียบร้อย ✅")
        self.load_requests()

    def update_detail_request(self):
        selected = self.get_selected_request_ids()
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกคำขอ OT ที่ต้องการบันทึกการแก้ไข")
            return
        if not confirm_dialog(self, "ยืนยัน", f"ต้องการบันทึกการแก้ไข {len(selected)} รายการหรือไม่?"):
            return
        for row_idx, req_id in selected:
            start_time = self.table.item(row_idx, 7).text()
            end_time = self.table.item(row_idx, 8).text()
            reason = self.table.item(row_idx, 9).text()
            jobdesc = self.table.item(row_idx, 10).text()
            update_ot_detail(req_id, start_time, end_time, reason, jobdesc)
        QMessageBox.information(self, "สำเร็จ", "บันทึกการแก้ไขเรียบร้อย ✅")
        self.load_requests()
