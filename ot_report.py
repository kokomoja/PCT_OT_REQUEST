import pandas as pd
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, \
    QComboBox, QDateEdit, QMessageBox
from PyQt5.QtCore import Qt, QDate
from db import get_ot_report

class OTReportForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("รายงานสรุป OT")
        self.resize(1000, 600)

        layout = QVBoxLayout()

        # ---- Filter ----
        filter_layout = QHBoxLayout()

        self.start_date = QDateEdit(calendarPopup=True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit(calendarPopup=True)
        self.end_date.setDate(QDate.currentDate())

        self.cmb_dept = QComboBox()
        self.cmb_dept.addItem("ทั้งหมด")
        self.cmb_emp = QComboBox()
        self.cmb_emp.addItem("ทั้งหมด")
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["ทั้งหมด", "Pending", "Approved", "Rejected"])

        filter_layout.addWidget(QLabel("เริ่ม:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("สิ้นสุด:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(QLabel("แผนก:"))
        filter_layout.addWidget(self.cmb_dept)
        filter_layout.addWidget(QLabel("พนักงาน:"))
        filter_layout.addWidget(self.cmb_emp)
        filter_layout.addWidget(QLabel("สถานะ:"))
        filter_layout.addWidget(self.cmb_status)

        self.btn_load = QPushButton("ดูรายงาน")
        self.btn_load.clicked.connect(self.load_report)
        filter_layout.addWidget(self.btn_load)

        layout.addLayout(filter_layout)

        # ---- Table ----
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "ชั่วโมง OT", "สถานะ"
        ])
        layout.addWidget(self.table)

        # ---- Export ----
        btn_layout = QHBoxLayout()
        self.btn_excel = QPushButton("Export Excel")
        self.btn_pdf = QPushButton("Export PDF")

        self.btn_excel.clicked.connect(self.export_excel)
        self.btn_pdf.clicked.connect(self.export_pdf)

        btn_layout.addWidget(self.btn_excel)
        btn_layout.addWidget(self.btn_pdf)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_report(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        dept = None if self.cmb_dept.currentText() == "ทั้งหมด" else self.cmb_dept.currentText()
        emp = None if self.cmb_emp.currentText() == "ทั้งหมด" else self.cmb_emp.currentText()
        status = None if self.cmb_status.currentText() == "ทั้งหมด" else self.cmb_status.currentText()

        rows = get_ot_report(start, end, dept, emp, status)
        self.table.setRowCount(len(rows))

        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)

    def export_excel(self):
        rows = []
        for i in range(self.table.rowCount()):
            row = []
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                row.append(item.text() if item else "")
            rows.append(row)

        if not rows:
            QMessageBox.warning(self, "เตือน", "ไม่มีข้อมูลสำหรับ Export")
            return

        df = pd.DataFrame(rows, columns=[
            "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "ชั่วโมง OT", "สถานะ"
        ])
        df.to_excel("ot_report.xlsx", index=False)
        QMessageBox.information(self, "สำเร็จ", "บันทึกไฟล์ ot_report.xlsx เรียบร้อย ✅")

    def export_pdf(self):
        # TODO: ใช้ reportlab ทำ PDF
        QMessageBox.information(self, "ยังไม่ทำ", "ฟังก์ชัน Export PDF กำลังพัฒนา")
