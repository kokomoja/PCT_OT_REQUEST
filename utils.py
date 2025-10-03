from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QLocale

def setup_dateedit(dateedit, format_str="yyyy-MM-dd"):
    """ตั้งค่า QDateEdit ให้ใช้เลขอารบิก และ format ตามต้องการ"""
    locale = QLocale(QLocale.English, QLocale.UnitedStates)
    dateedit.setLocale(locale)
    dateedit.setDisplayFormat(format_str)
    return dateedit

def setup_timeedit(timeedit, format_str="HH:mm:ss"):
    """ตั้งค่า QTimeEdit ให้ใช้เลขอารบิก และ format ตามต้องการ"""
    locale = QLocale(QLocale.English, QLocale.UnitedStates)
    timeedit.setLocale(locale)
    timeedit.setDisplayFormat(format_str)
    return timeedit

def thai_to_arabic(text: str) -> str:
    """แปลงเลขไทยเป็นเลขอารบิก (ใช้ทุกที่—รวมศูนย์ฟังก์ชันที่นี่)"""
    if not text:
        return ""
    trans = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
    return str(text).translate(trans)

def confirm_dialog(parent, title, message) -> bool:
    """Popup ยืนยันแบบใช้งานซ้ำ"""
    reply = QMessageBox.question(
        parent, title, message,
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    return reply == QMessageBox.Yes
