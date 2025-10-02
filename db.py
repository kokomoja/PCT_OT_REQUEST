import pyodbc

DB_CONFIG = {
    "server": "192.168.99.253,1433",   # ✅ ปรับตาม environment จริงของคุณ
    "database": "otPCT",
    "username": "sa",
    "password": "@1234",
    "driver": "{ODBC Driver 17 for SQL Server}"
}

def get_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']}"
    )
    return pyodbc.connect(conn_str)


# ---------------- INSERT ----------------
def insert_ot_request(employee_code, employee_name, department, position,
                      ot_date, start_time, end_time, ot_reason, job_description):
    """บันทึกคำขอ OT ใหม่ โดยอ้างอิง employee_code"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO OT_Request
            (employee_code, employee_name, department, position,
             ot_date, start_time, end_time, ot_reason, job_description, submitted_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), 'Pending')
    """, (employee_code, employee_name, department, position,
          ot_date, start_time, end_time, ot_reason, job_description))
    conn.commit()
    conn.close()


# ---------------- SELECT ----------------
def get_last_ot_requests(employee_code, limit=10):
    """ดึงประวัติการบันทึก OT ตาม employee_code"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP {limit}
            request_id, employee_code, employee_name,
            department, position, ot_date, start_time, end_time, ot_reason, status
        FROM OT_Request
        WHERE employee_code = ?
        ORDER BY request_id DESC
    """, (employee_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------- DELETE ----------------
def delete_ot_request(request_id):
    """ลบคำขอ OT ตาม request_id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM OT_Request WHERE request_id = ?", (request_id,))
    conn.commit()
    conn.close()

# ---------------- ADMIN SELECT ----------------
def get_pending_ot_requests():
    """ดึงคำขอ OT ที่ยัง Pending"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT request_id, employee_code, employee_name, department, position,
               ot_date, start_time, end_time, ot_reason, job_description, status
        FROM OT_Request
        WHERE status = 'Pending'
        ORDER BY submitted_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


# ---------------- ADMIN UPDATE ----------------
def update_ot_status(request_id, status, approver_code, reason=None):
    """อัพเดทสถานะ OT (Approve/Reject)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE OT_Request
        SET status = ?, approver_code = ?, approved_at = GETDATE(), reject_reason = ?
        WHERE request_id = ?
    """, (status, approver_code, reason, request_id))
    conn.commit()
    conn.close()
    
def update_ot_time(request_id, start_time, end_time):
    """อัปเดตเวลาเริ่มและสิ้นสุดของ OT Request"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE OT_Request
        SET start_time = ?, end_time = ?
        WHERE request_id = ?
    """, (start_time, end_time, request_id))
    conn.commit()
    conn.close()    

def get_ot_report(start_date=None, end_date=None, department=None, employee_code=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT request_id, employee_code, employee_name, department, position,
               ot_date, start_time, end_time,
               DATEDIFF(MINUTE, start_time, end_time) / 60.0 AS ot_hours,
               ot_reason, status
        FROM OT_Request
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND ot_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND ot_date <= ?"
        params.append(end_date)
    if department:
        query += " AND department = ?"
        params.append(department)
    if employee_code:
        query += " AND employee_code = ?"
        params.append(employee_code)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY ot_date DESC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows
