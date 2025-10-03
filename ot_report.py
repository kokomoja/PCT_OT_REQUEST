import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from db import get_ot_report, get_departments, get_employees
from utils import setup_dateedit, thai_to_arabic


class OTReportForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("รายงานสรุป OT")
        self.resize(1150, 650)

        layout = QVBoxLayout()

        # ---- Filter ----
        row_filter = QHBoxLayout()
        row_filter.setAlignment(Qt.AlignLeft)   # ✅ ชิดซ้ายทั้งหมด

        self.start_date = setup_dateedit(QDateEdit(calendarPopup=True))
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setFixedWidth(95)
        
        self.end_date = setup_dateedit(QDateEdit(calendarPopup=True))
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setFixedWidth(95)
        
        self.cmb_dept = QComboBox()
        self.cmb_dept.addItem("ทั้งหมด")
        self.cmb_dept.setFixedWidth(110)
        for d in get_departments():
            self.cmb_dept.addItem(d)

        self.cmb_emp = QComboBox()
        self.cmb_emp.addItem("ทั้งหมด")
        self.cmb_emp.setFixedWidth(250)
        for code, name in get_employees():
            self.cmb_emp.addItem(f"{code} - {name}")

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["ทั้งหมด", "Pending", "Approved", "Rejected"])
        self.cmb_status.setFixedWidth(110)
        self.btn_load = QPushButton("ดูรายงาน")
        self.btn_load.clicked.connect(self.load_report)

        # ✅ เพิ่ม widget เรียงชิดซ้าย
        row_filter.addWidget(QLabel("เริ่ม:"))
        row_filter.addWidget(self.start_date)
        row_filter.addWidget(QLabel("สิ้นสุด:"))
        row_filter.addWidget(self.end_date)
        row_filter.addWidget(QLabel("แผนก:"))
        row_filter.addWidget(self.cmb_dept)
        row_filter.addWidget(QLabel("พนักงาน:"))
        row_filter.addWidget(self.cmb_emp)
        row_filter.addWidget(QLabel("สถานะ:"))
        row_filter.addWidget(self.cmb_status)
        row_filter.addWidget(self.btn_load)

        layout.addLayout(row_filter)

        # ---- Table ----
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "ชั่วโมง OT", "เหตุผล", "สถานะ"
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

    def _parse_emp_selection(self, text):
        if text == "ทั้งหมด":
            return None
        code = text.split(" - ", 1)[0].strip()
        return code or None

    def load_report(self):
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        dept = None if self.cmb_dept.currentText() == "ทั้งหมด" else self.cmb_dept.currentText()
        emp_code = self._parse_emp_selection(self.cmb_emp.currentText())
        status = None if self.cmb_status.currentText() == "ทั้งหมด" else self.cmb_status.currentText()

        rows = get_ot_report(start, end, dept, emp_code, status)
        self.table.setRowCount(len(rows))
        
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                text = thai_to_arabic(str(value))

                if j == 8:  # ชั่วโมง OT
                    try:
                        text = f"{float(value):.2f}"
                    except Exception:
                        text = "0.00"

                item = QTableWidgetItem(text)

                if j in [2, 9]:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignCenter)

                if j == 10:
                    status_txt = str(value)
                    if status_txt == "Approved":
                        item.setBackground(QColor(220, 255, 220))
                    elif status_txt == "Rejected":
                        item.setBackground(QColor(255, 220, 220))
                    else:
                        item.setBackground(QColor(255, 249, 196))

                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(9, max(self.table.columnWidth(9), 320))

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
            "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "ชั่วโมง OT", "เหตุผล", "สถานะ"
        ])
        df.to_excel("ot_report.xlsx", index=False)
        QMessageBox.information(self, "สำเร็จ", "บันทึกไฟล์ ot_report.xlsx เรียบร้อย ✅")

    def export_pdf(self):
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os

            # ✅ โหลดฟอนต์ภาษาไทย (ต้องมีไฟล์ TTF อยู่ในโฟลเดอร์ fonts/)
            font_path = os.path.join(os.path.dirname(__file__), "fonts", "THSarabunNew.ttf")
            pdfmetrics.registerFont(TTFont("THSarabunNew", font_path))

            # ✅ กำหนด stylesheet ที่รองรับภาษาไทย
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name="ThaiNormal", fontName="THSarabunNew", fontSize=14, leading=16))
            styles.add(ParagraphStyle(name="ThaiTitle", fontName="THSarabunNew-Bold", fontSize=18, leading=20, alignment=1))

            data = [[
                "ID", "รหัส", "ชื่อ", "แผนก", "ตำแหน่ง",
                "วันที่", "เวลาเริ่ม", "เวลาสิ้นสุด", "ชั่วโมง OT", "เหตุผล", "สถานะ"
            ]]
            for i in range(self.table.rowCount()):
                row = []
                for j in range(self.table.columnCount()):
                    item = self.table.item(i, j)
                    row.append(item.text() if item else "")
                data.append(row)

            if len(data) == 1:
                QMessageBox.warning(self, "เตือน", "ไม่มีข้อมูลสำหรับ Export")
                return

            doc = SimpleDocTemplate(
                "ot_report.pdf",
                pagesize=landscape(A4),
                leftMargin=18, rightMargin=18, topMargin=18, bottomMargin=18
            )

            elems = []
            elems.append(Paragraph("รายงานสรุป OT", styles["ThaiTitle"]))
            elems.append(Spacer(1, 8))

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#01579B")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,-1), 'THSarabunNew'),   # ✅ บังคับใช้ฟอนต์ไทย
                ('FONTSIZE', (0,0), (-1,-1), 12),
                ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.HexColor("#F5F5F5")]),
            ]))

            elems.append(table)
            doc.build(elems)
            QMessageBox.information(self, "สำเร็จ", "บันทึกไฟล์ ot_report.pdf เรียบร้อย ✅")
        except Exception as e:
            QMessageBox.critical(self, "ผิดพลาด", f"Export PDF ล้มเหลว: {e}")

