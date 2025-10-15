from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QMessageBox, QLabel, QDateEdit, QTimeEdit, QHeaderView,
    QTableWidget, QTableWidgetItem, QCheckBox, QSpacerItem, QSizePolicy, QComboBox
)
from PyQt5.QtCore import QDate, QTime, QDateTime, QLocale, QTimer, Qt
from db import insert_ot_request, get_last_ot_requests, delete_ot_request, update_ot_time_by_employee
from utils import setup_dateedit, setup_timeedit, thai_to_arabic, confirm_dialog


class OTForm(QWidget):
    def __init__(self, login_window):
        super().__init__()
        self.setWindowTitle("คำขอทำงานล่วงเวลา (OT Request)")
        self.resize(950, 700)
        self.login_window = login_window
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        row_top = QHBoxLayout()
        self.countdown_label = QLabel("เหลือเวลา ...")
        self.countdown_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: red;")
        row_top.addWidget(self.countdown_label, alignment=Qt.AlignLeft)

        row_top.addStretch(1)

        self.logout_btn = QPushButton(" Logout ")
        self.logout_btn.clicked.connect(self.logout)
        row_top.addWidget(self.logout_btn, alignment=Qt.AlignRight)

        layout.addLayout(row_top)

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
        
        row1.addWidget(QLabel("รหัสพนักงาน :"))
        row1.addWidget(self.employee_code)
        row1.addWidget(QLabel("ชื่อ–นามสกุล :"))
        row1.addWidget(self.employee_name)
        row1.addWidget(QLabel("แผนก :"))
        row1.addWidget(self.department)
        row1.addWidget(QLabel("ตำแหน่ง :"))
        row1.addWidget(self.position)

        row1.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(row1)

        self.ot_date = setup_dateedit(QDateEdit(calendarPopup=True))
        self.ot_date.setDate(QDate.currentDate())
        self.ot_date.setFixedWidth(100)

        self.start_time = setup_timeedit(QTimeEdit())
        self.start_time.setTime(QTime(18, 0))
        self.start_time.setFixedWidth(80)

        self.end_time = setup_timeedit(QTimeEdit())
        self.end_time.setTime(QTime(22, 0))
        self.end_time.setFixedWidth(80)

        row2 = QHBoxLayout()
        row2.setAlignment(Qt.AlignLeft)
        row2.addWidget(QLabel("วันที่ทำ OT :"))
        row2.addWidget(self.ot_date)
        row2.addWidget(QLabel("เวลาเริ่ม :"))
        row2.addWidget(self.start_time)
        row2.addWidget(QLabel("เวลาสิ้นสุด :"))
        row2.addWidget(self.end_time)
        layout.addLayout(row2)

        locale = QLocale(QLocale.English, QLocale.UnitedStates)
        self.ot_date.setLocale(locale)
        self.start_time.setLocale(locale)
        self.end_time.setLocale(locale)

        row_reason = QHBoxLayout()
        row_reason.setAlignment(Qt.AlignLeft)

        row_reason.addWidget(QLabel("เหตุผลในการขอโอที :"))
        self.ot_reason = QComboBox()
        self.ot_reason.addItems([
            "ทำงานล่วงเวลาในเวลาทำการ",
            "ทำงานในวันหยุดประจำสัปดาห์",
            "ทำงานในวันหยุดนักขัตฤกษ์"
        ])
        self.ot_reason.setFixedWidth(300)
        row_reason.addWidget(self.ot_reason)

        row_reason.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        layout.addLayout(row_reason)

        layout.addWidget(QLabel("รายละเอียดงาน :"))
        self.job_description = QTextEdit()
        self.job_description.setFixedHeight(100)
        layout.addWidget(self.job_description)

        row_btn = QHBoxLayout()
        row_btn.setAlignment(Qt.AlignLeft)

        self.save_btn = QPushButton("💾 บันทึกคำขอ")
        self.save_btn.clicked.connect(self.save_request)
        self.save_btn.setFixedSize(180, 45)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;   /* เขียวมรกต */
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
                color: #f0f0f0;
            }
        """)
        row_btn.addWidget(self.save_btn)
        row_btn.addSpacing(20)

        self.update_time_btn = QPushButton("🕒 อัปเดตเวลา OT ที่เลือก")
        self.update_time_btn.clicked.connect(self.update_selected_time)
        self.update_time_btn.setFixedSize(230, 45)
        self.update_time_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;   /* ฟ้าน้ำทะเล */
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
                color: #f0f0f0;
            }
        """)
        row_btn.addWidget(self.update_time_btn)
        row_btn.addSpacing(20)

        self.delete_btn = QPushButton("🗑️ ลบที่เลือก")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(True)
        self.delete_btn.setFixedSize(180, 45)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;   /* แดงสด */
                color: white;
                font-size: 16pt;
                font-weight: bold;
                border-radius: 10px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:disabled {
                background-color: #9E9E9E;
                color: #f0f0f0;
            }
        """)
        row_btn.addWidget(self.delete_btn)

        layout.addLayout(row_btn)


        self.save_info = QLabel("")
        self.save_info.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.save_info)

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
        self.table.setColumnWidth(8, 200)
        self.table.setColumnWidth(9, 120)
        layout.addWidget(self.table)

        self.setLayout(layout)

        self._blink = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.timeout.connect(self.check_button_enabled)
        self.timer.start(1000)

    def check_button_enabled(self):
        """ตรวจเวลาและสถานะ checkbox เพื่อควบคุมปุ่มบันทึก"""
        now = QTime.currentTime()
        any_checked = any(
            self.table.cellWidget(i, 0) and self.table.cellWidget(i, 0).isChecked()
            for i in range(self.table.rowCount())
        )

        if any_checked:
            self.save_btn.setEnabled(False)
            self.save_info.setText("🚫 ปิดการบันทึกขณะเลือกแก้ไขข้อมูล OT")
            return

        if QTime(8, 0, 0) <= now <= QTime(23, 59, 59):
            self.save_btn.setEnabled(True)
            self.save_info.setText("")
        else:
            self.save_btn.setEnabled(False)
            self.save_info.setText("⏰ สามารถบันทึกได้เฉพาะเวลา 12:00–24:00 น.")

    def can_delete_today(self, request_date):
        return request_date == QDate.currentDate()

    def save_request(self):
        try:
            emp_code = self.employee_code.text()
            emp_name = self.employee_name.text()
            dept = self.department.text()
            pos = self.position.text()
            ot_date = thai_to_arabic(self.ot_date.date().toString("yyyy-MM-dd"))
            start_time = "00:00:00"  # ✅ ค่าเริ่มต้น
            end_time = "00:00:00"
            reason = self.ot_reason.currentText()
            job = self.job_description.toPlainText()

            insert_ot_request(emp_code, emp_name, dept, pos, ot_date, start_time, end_time, reason, job)
            QMessageBox.information(self, "สำเร็จ", "บันทึกคำขอ OT เรียบร้อย (เวลา 00:00:00)")
            self.load_last_requests(emp_code)
            self.check_checkbox_selection()        
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

    def update_selected_time(self):
        """อัปเดตเวลาเฉพาะรายการที่ถูกติ๊กเท่านั้น"""
        selected = []
        for i in range(self.table.rowCount()):
            chk = self.table.cellWidget(i, 0)
            if chk and chk.isChecked():  
                req_id = self.table.item(i, 1).data(Qt.UserRole)
                selected.append((i, req_id))
        if not selected:
            QMessageBox.warning(self, "เตือน", "กรุณาเลือกรายการที่จะอัปเดตเวลา")
            return
        if not confirm_dialog(self, "ยืนยัน", f"ต้องการอัปเดต {len(selected)} รายการหรือไม่?"):
            return

        emp_code = self.employee_code.text().strip()
        new_start = self.start_time.time().toString("HH:mm:ss")
        new_end = self.end_time.time().toString("HH:mm:ss")
        updated = 0
        errors = []

        for _, req_id in selected:
            try:
                update_ot_time_by_employee(req_id, new_start, new_end, emp_code)
                updated += 1
            except Exception as e:
                errors.append(str(e))
        if updated > 0:
            QMessageBox.information(self, "สำเร็จ", f"อัปเดตเวลา {updated} รายการเรียบร้อย")
        if errors:
            QMessageBox.warning(self, "ข้อผิดพลาดบางส่วน", "\n".join(errors))
        self.load_last_requests(emp_code)
        self.check_checkbox_selection()

            
    def load_last_requests(self, employee_code=None):
        """โหลดประวัติคำขอ OT ของพนักงาน"""
        rows = get_last_ot_requests(employee_code, 10) if employee_code else []
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            checkbox = QCheckBox()
            checkbox.setStyleSheet("margin-left:10px;")
            checkbox.stateChanged.connect(self.check_checkbox_selection)

            status_text = str(row.status).strip().lower()
            ot_date = QDate.fromString(str(row.ot_date), "yyyy-MM-dd")
            days_diff = ot_date.daysTo(QDate.currentDate())

            if status_text != "pending" or days_diff > 3:
                checkbox.setEnabled(False)
                if status_text != "pending":
                    checkbox.setToolTip("อนุมัติหรือปฏิเสธแล้ว - ไม่สามารถแก้ไขได้")
                elif days_diff > 3:
                    checkbox.setToolTip(f"เกินกำหนด 3 วัน ({days_diff} วันแล้ว) - ไม่สามารถแก้ไขได้")

            self.table.setCellWidget(i, 0, checkbox)


            blank_item = QTableWidgetItem("")
            blank_item.setFlags(Qt.NoItemFlags)  
            self.table.setItem(i, 0, blank_item)

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
                QTableWidgetItem(str(row.job_description)),
                QTableWidgetItem(str(row.status)),
            ]

            submitted_text = ""
            try:
                submitted_text = row.submitted_at.strftime("%Y-%m-%d %H:%M")
            except Exception:
                submitted_text = str(row.submitted_at)
            row_values.append(QTableWidgetItem(submitted_text))

            for j, item in enumerate(row_values):
                if j == 6:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j + 1, item)

            start_val = str(row.start_time).strip()
            end_val = str(row.end_time).strip()
            if start_val in ["00:00:00", "None", "null", ""] or end_val in ["00:00:00", "None", "null", ""]:
                for j in range(1, self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setBackground(Qt.yellow)

            if status_text == "approved":
                for j in range(1, self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setBackground(Qt.lightGray)
                        item.setForeground(Qt.darkGreen)

            if status_text == "rejected":
                for j in range(1, self.table.columnCount()):
                    item = self.table.item(i, j)
                    if item:
                        item.setBackground(Qt.white)
                        item.setForeground(Qt.red)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(7, 180)
        self.table.setColumnWidth(8, 500)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 20)

    def check_checkbox_selection(self):
        """ตรวจ checkbox ทั้งหมด แล้วปรับสถานะปุ่มต่าง ๆ"""
        any_checked = any(
            self.table.cellWidget(i, 0) and self.table.cellWidget(i, 0).isChecked()
            for i in range(self.table.rowCount())
        )
        self.save_btn.setEnabled(not any_checked)
        self.update_time_btn.setEnabled(any_checked)
        self.delete_btn.setEnabled(any_checked)

    def clear_form(self, clear_employee=True):
        self.ot_reason.setCurrentIndex(0)
        self.job_description.clear()
        self.ot_date.setDate(QDate.currentDate())
        self.start_time.setTime(QTime(17, 0))
        self.end_time.setTime(QTime(22, 0))
        self.table.setRowCount(0)

    def update_countdown(self):
        now = QDateTime.currentDateTime()
        target = QDateTime(now.date(), QTime(23, 59, 59))
        secs = now.secsTo(target)
        if secs > 0:
            h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
            self.countdown_label.setText(f"เหลือเวลา {h:02}:{m:02}:{s:02}")
        else:
            self.countdown_label.setText("เลยเวลาขอ OT แล้ว")
            self.countdown_label.setStyleSheet("color: gray; font-weight: bold;")

    def logout(self):
        if not confirm_dialog(self, "ยืนยันการออกจากระบบ", "คุณแน่ใจหรือไม่ว่าต้องการออกจากระบบ?"):
            return
        self.close()
        self.login_window.clear_fields()
        self.login_window.show()
