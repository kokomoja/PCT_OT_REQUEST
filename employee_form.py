# employee_form.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QMessageBox, QComboBox, QLabel, QInputDialog
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from db import get_connection


class EmployeeForm(QWidget):
    """ฟอร์มเพิ่มรายชื่อพนักงาน สำหรับ Admin"""
    SECRET_CODE = "0845535000721"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("👨‍💼 เพิ่มรายชื่อพนักงาน")
        self.resize(420, 400)

        self.setFont(QFont("TH Sarabun New", 16))

        layout = QVBoxLayout()
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(10)

        self.txt_name = QLineEdit()
        self.txt_department = QLineEdit()
        self.txt_position = QLineEdit()
        self.txt_code = QLineEdit()
        self.txt_password = QLineEdit("1")
        self.txt_password.setEchoMode(QLineEdit.Normal)

        self.cmb_auth = QComboBox()
        self.cmb_auth.addItems(["user", "admin"])

        form.addRow("ชื่อพนักงาน:", self.txt_name)
        form.addRow("แผนก:", self.txt_department)
        form.addRow("ตำแหน่ง:", self.txt_position)
        form.addRow("รหัสพนักงาน:", self.txt_code)
        form.addRow("Password:", self.txt_password)
        form.addRow("สิทธิ์ (Auth):", self.cmb_auth)

        layout.addLayout(form)

        self.btn_save = QPushButton("💾 บันทึกข้อมูลพนักงาน")
        self.btn_save.clicked.connect(self.save_employee)
        layout.addWidget(self.btn_save, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def save_employee(self):
        """ฟังก์ชันบันทึกข้อมูลพนักงานใหม่"""
        name = self.txt_name.text().strip()
        dept = self.txt_department.text().strip()
        pos = self.txt_position.text().strip()
        code = self.txt_code.text().strip()
        pwd = self.txt_password.text().strip()
        auth = self.cmb_auth.currentText().strip()

        if not all([name, dept, pos, code, pwd, auth]):
            QMessageBox.warning(self, "⚠️ เตือน", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
            return

        secret, ok = QInputDialog.getText(
            self, "🔒 ยืนยันรหัสลับ",
            "กรุณากรอกรหัสลับเพื่ออนุญาตการบันทึก:",
        )

        if not ok:
            QMessageBox.information(self, "ยกเลิก", "ยกเลิกการบันทึกข้อมูล")
            return

        if secret.strip() != self.SECRET_CODE:
            QMessageBox.critical(self, "❌ รหัสไม่ถูกต้อง", "รหัสลับไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM Employee WHERE employee_code = ?", (code,))
            exists = cursor.fetchone()[0]
            if exists > 0:
                QMessageBox.warning(self, "⚠️ พบข้อมูลซ้ำ", f"รหัสพนักงาน {code} มีอยู่ในระบบแล้ว")
                conn.close()
                return

            cursor.execute("""
                INSERT INTO Employee (employee_name, department, position, employee_code, employee_password, employee_auth)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, dept, pos, code, pwd, auth))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "✅ สำเร็จ", "เพิ่มข้อมูลพนักงานเรียบร้อยแล้ว")
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "❌ ข้อผิดพลาด", f"ไม่สามารถบันทึกได้:\n{str(e)}")

    def clear_form(self):
        """เคลียร์ข้อมูลหลังบันทึก"""
        self.txt_name.clear()
        self.txt_department.clear()
        self.txt_position.clear()
        self.txt_code.clear()
        self.txt_password.setText("1")
        self.cmb_auth.setCurrentIndex(0)
