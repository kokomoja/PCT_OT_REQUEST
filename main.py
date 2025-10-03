from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QMessageBox, QLabel, QDateEdit, QTimeEdit,
    QTableWidget, QTableWidgetItem, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import QDate, QTime, QDateTime, QLocale, QTimer, Qt
from db import insert_ot_request, get_last_ot_requests, delete_ot_request
from utils import setup_dateedit, setup_timeedit, thai_to_arabic, confirm_dialog


class OTForm(QWidget):
    def __init__(self, login_window):
        super().__init__()
        self.setWindowTitle("คำขอทำงานล่วงเวลา (OT Request)")
        self.resize(950, 700)
        self.login_window = login_window   # ✅ reference กลับไป LoginForm

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # ---- บรรทัดบนสุด: Label + Logout ----
        row_top = QHBoxLayout()

        # ✅ Label นับเวลาถอยหลัง (ชิดซ้าย)
        self.countdown_label = QLabel("เหลือเวลา ...")
        self.countdown_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: red;")
        row_top.addWidget(self.countdown_label, alignment=Qt.AlignLeft)

        # ✅ Spacer กลาง
        row_top.addStretch(1)

        # ✅ ปุ่มออกจากระบบ (ชิดขวาสุด)
        self.logout_btn = QPushButton("ออกจากระบบ")
        self.logout_btn.clicked.connect(self.logout)
        row_top.addWidget(self.logout_btn, alignment=Qt.AlignRight)

        layout.addLayout(row_top)

        # --- Employee info ---
        self.employee_code = QLineEdit()
        self.employee_code.setFixedWidth(60)
        self.employee_name = QLineEdit()
        self.employee_name.setFixedWidth(150)
        self.department = QLineEdit()
        self.department.setFixedWidth(100)
        self.position = QLineEdit()
        self.position.setFixedWidth(150)

        for field in (self.employee_code, self.employee_name, self.department, self.position):
            field.setReadOnly(True)

        row1 = QHBoxLayout()
        row1.setAlignment(Qt.AlignLeft)  
        
        row1.addWidget(QLabel("รหัสพนักงาน:"))
        row1.addWidget(self.employee_code)
        row1.addWidget(QLabel("ชื่อ–นามสกุล:"))
        row1.addWidget(self.employee_name)
        row1.addWidget(QLabel("แผนก:"))
        row1.addWidget(self.department)
        row1.addWidget(QLabel("ตำแหน่ง:"))
        row1.addWidget(self.position)

        row1.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(row1)

        # --- OT Date + Time ---
        self.ot_date = setup_dateedit(QDateEdit(calendarPopup=True))
        self.ot_date.setDate(QDate.currentDate())
        self.ot_date.setFixedWidth(100)
        self.ot_date.setEnabled(False)

        self.start_time = setup_timeedit(QTimeEdit())
        self.start_time.setTime(QTime(18, 0))
        self.start_time.setFixedWidth(80)

        self.end_time = setup_timeedit(QTimeEdit())
        self.end_time.setTime(QTime(22, 0))
        self.end_time.setFixedWidth(80)

        row2 = QHBoxLayout()
        row2.setAlignment(Qt.AlignLeft)
        row2.addWidget(QLabel("วันที่ทำ OT:"))
        row2.addWidget(self.ot_date)
        row2.addWidget(QLabel("เวลาเริ่ม:"))
        row2.addWidget(self.start_time)
        row2.addWidget(QLabel("เวลาสิ้นสุด:"))
        row2.addWidget(self.end_time)
        layout.addLayout(row2)

        # locale
        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.ot_date.setLocale(locale)
        self.start_time.setLocale(locale)
        self.end_time.setLocale(locale)

        # --- Reason & Job ---
        layout.addWidget(QLabel("เหตุผลการขอ OT:"))
        self.ot_reason = QTextEdit()
        self.ot_reason.setFixedHeight(60)
        layout.addWidget(self.ot_reason)

        layout.addWidget(QLabel("รายละเอียดงาน:"))
        self.job_description = QTextEdit()
        self.job_description.setFixedHeight(100)
        layout.addWidget(self.job_description)

        # --- Buttons ---
        self.save_btn = QPushButton("บันทึกคำขอ")
        self.save_btn.clicked.connect(self.save_request)

        self.delete_btn = QPushButton("ลบที่เลือก")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(True)

        row_btn = QHBoxLayout()
        row_btn.setAlignment(Qt.AlignLeft)
        row_btn.addWidget(self.save_btn)
        row_btn.addSpacing(20)
        row_btn.addWidget(self.delete_btn)
        layout.addLayout(row_btn)

        self.save_info = QLabel("")
        self.save_info.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.save_info)

        # --- Table ---
        layout.addWidget(QLabel("ประวัติการบันทึก OT:"))
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "เลือก", "รหัสพนักงาน", "ชื่อ", "แผนก",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "เหตุผล", "สถานะ", "บันทึกเวลา"
        ])
        self.table.setColumnWidth(0, 20)
        self.table.setColumnWidth(1, 75)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 200)
        self.table.setColumnWidth(8, 80)
        self.table.setColumnWidth(9, 120)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Timer
        self._blink = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.timeout.connect(self.check_button_enabled)
        self.timer.start(1000)

    # ---------------- Helper ----------------
    def check_button_enabled(self):
        now = QTime.currentTime()
        if QTime(8, 0, 0) <= now <= QTime(17, 0, 0):
            self.save_btn.setEnabled(True)
            self.save_info.setText("")
        else:
            self.save_btn.setEnabled(False)
            self.save_info.setText("⏰ สามารถบันทึกได้เฉพาะเวลา 08:00–17:00 น.")

    def can_delete_today(self, request_date):
        return request_date == QDate.currentDate()

    # ---------------- Functions ----------------
    def save_request(self):
        try:
            employee_code = self.employee_code.text()
            employee_name = self.employee_name.text()
            department = self.department.text()
            position = self.position.text()
            ot_date = thai_to_arabic(self.ot_date.date().toString("yyyy-MM-dd"))
            start_time = thai_to_arabic(self.start_time.time().toString("HH:mm:ss"))
            end_time = thai_to_arabic(self.end_time.time().toString("HH:mm:ss"))
            ot_reason = self.ot_reason.toPlainText()
            job_description = self.job_description.toPlainText()

            insert_ot_request(employee_code, employee_name, department, position,
                              ot_date, start_time, end_time, ot_reason, job_description)

            QMessageBox.information(self, "สำเร็จ", "บันทึกคำขอ OT เรียบร้อยแล้ว ✅")
            self.clear_form(False)
            self.load_last_requests(employee_code)

        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

    def delete_selected(self):
        rows_to_delete = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                request_id = self.table.item(i, 1).data(Qt.UserRole)
                rows_to_delete.append((i, request_id))

        if not rows_to_delete:
            QMessageBox.warning(self, "ไม่พบการเลือก", "กรุณาเลือกอย่างน้อย 1 รายการ")
            return

        if not confirm_dialog(self, "ยืนยันการลบ", f"คุณต้องการลบ {len(rows_to_delete)} รายการ ใช่หรือไม่?"):
            return

        for row, request_id in sorted(rows_to_delete, reverse=True):
            delete_ot_request(request_id)
            self.table.removeRow(row)

        QMessageBox.information(self, "สำเร็จ", "ลบคำขอที่เลือกเรียบร้อยแล้ว ✅")

    def load_last_requests(self, employee_code=None):
        rows = get_last_ot_requests(employee_code, 10) if employee_code else []
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:10px;")
            request_date = QDate.fromString(str(row.ot_date), "yyyy-MM-dd")
            if not self.can_delete_today(request_date):
                checkbox.setEnabled(False)
            self.table.setCellWidget(i, 0, checkbox)

            item_code = QTableWidgetItem(str(row.employee_code))
            item_code.setData(Qt.UserRole, row.request_id)

            row_values = [
                item_code,
                QTableWidgetItem(str(row.employee_name)),
                QTableWidgetItem(str(row.department)),
                QTableWidgetItem(thai_to_arabic(str(row.ot_date))),
                QTableWidgetItem(thai_to_arabic(str(row.start_time))),
                QTableWidgetItem(thai_to_arabic(str(row.end_time))),
                QTableWidgetItem(str(row.ot_reason)),
                QTableWidgetItem(str(row.status)),
            ]

            # ✅ เพิ่มคอลัมน์ submitted_at
            submitted_text = ""
            try:
                submitted_text = row.submitted_at.strftime("%Y-%m-%d %H:%M")
            except Exception:
                submitted_text = str(row.submitted_at)
            row_values.append(QTableWidgetItem(submitted_text))

            for j, item in enumerate(row_values):
                if j == 6:  # ot_reason
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j + 1, item)

    def clear_form(self, clear_employee=True):
        self.ot_reason.clear()
        self.job_description.clear()
        self.ot_date.setDate(QDate.currentDate())
        self.start_time.setTime(QTime(17, 0))
        self.end_time.setTime(QTime(22, 0))
        self.table.setRowCount(0)

    def update_countdown(self):
        now = QDateTime.currentDateTime()
        target = QDateTime(now.date(), QTime(17, 0, 0))
        secs = now.secsTo(target)
        if secs > 0:
            h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
            self.countdown_label.setText(f"เหลือเวลา {h:02}:{m:02}:{s:02}")
        else:
            self.countdown_label.setText("เลยเวลา 17:00 แล้ว")
            self.countdown_label.setStyleSheet("color: gray; font-weight: bold;")

    def logout(self):
        if not confirm_dialog(self, "ยืนยันการออกจากระบบ", "คุณแน่ใจหรือไม่ว่าต้องการออกจากระบบ?"):
            return
        self.close()
        self.login_window.clear_fields()
        self.login_window.show()
