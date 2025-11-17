import pyodbc
import os
from dotenv import load_dotenv
from datetime import datetime, time

# โหลด .env
load_dotenv()

DB_CONFIG = {
    "driver": os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}"),
    "server": os.getenv("DB_SERVER", "localhost,1433"),
    "database": os.getenv("DB_NAME", "otPCT"),
    "username": os.getenv("DB_USER", "sa"),
    "password": os.getenv("DB_PASS", ""),
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


# ================================================
#     ฟังก์ชันสำหรับ OT Request (ต้องมี)
# ================================================

def insert_ot_request(employee_code, employee_name, department, position,
                      ot_date, start_time, end_time, ot_reason, job_description):
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


def get_last_ot_requests(employee_code, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT TOP {limit}
            request_id,
            employee_code,
            employee_name,
            department,
            position,
            ot_date,
            start_time,
            end_time,
            ot_reason,
            job_description,
            status,
            submitted_at
        FROM OT_Request
        WHERE employee_code = ?
        ORDER BY request_id DESC
    """, (employee_code,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_ot_request(request_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM OT_Request WHERE request_id = ?", (request_id,))
    conn.commit()
    conn.close()


def get_all_ot_requests(status=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT request_id, employee_code, employee_name, department, position,
               ot_date, start_time, end_time, ot_reason, job_description, status
        FROM OT_Request
    """
    params = []
    if status:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY submitted_at DESC"

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_ot_status(request_id, status, approver_code, reason=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE OT_Request
        SET status = ?, approver_code = ?, approved_at = GETDATE(), reject_reason = ?
        WHERE request_id = ?
    """, (status, approver_code, reason, request_id))
    conn.commit()
    conn.close()


def update_ot_detail(request_id, start_time, end_time, ot_reason, job_description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE OT_Request
        SET start_time = ?, end_time = ?, ot_reason = ?, job_description = ?
        WHERE request_id = ?
    """, (start_time, end_time, ot_reason, job_description, request_id))
    conn.commit()
    conn.close()


def update_ot_time_by_employee(request_id, start_time, end_time, employee_code):
    """พนักงานอัปเดตเวลา OT ของตัวเอง (เฉพาะ Pending หรือ Approved)"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        def to_time(value):
            if isinstance(value, time):
                return value
            if isinstance(value, datetime):
                return value.time()
            if isinstance(value, str):
                parts = value.strip().split(":")
                if len(parts) == 2:
                    h, m = int(parts[0]), int(parts[1])
                    return time(h, m, 0)
                elif len(parts) == 3:
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                    return time(h, m, s)
            raise ValueError(f"รูปแบบเวลาไม่ถูกต้อง: {value}")

        start_t = to_time(start_time)
        end_t = to_time(end_time)

        cursor.execute("""
            SELECT status, employee_code
            FROM OT_Request
            WHERE request_id = ?
        """, (request_id,))
        result = cursor.fetchone()
        if not result:
            raise Exception("ไม่พบคำขอ OT ที่ระบุ")

        cursor.execute("""
            UPDATE OT_Request
            SET start_time = ?, end_time = ?
            WHERE request_id = ?
              AND employee_code = ?
              AND status IN ('Pending', 'Approved')
        """, (start_t, end_t, request_id, employee_code))

        if cursor.rowcount == 0:
            raise Exception("ไม่สามารถอัปเดตได้ (อาจถูกอนุมัติ/ปฏิเสธแล้ว หรือรหัสพนักงานไม่ตรง)")

        conn.commit()
        conn.close()

    except Exception as e:
        conn.rollback()
        conn.close()
        raise Exception(f"อัปเดตเวลาไม่สำเร็จ: {e}")


def get_ot_report(start_date=None, end_date=None, department=None, employee_code=None, status=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT 
            request_id, employee_code, employee_name, department, position,
            ot_date, start_time, end_time,
            CASE 
                WHEN TRY_CONVERT(TIME, start_time) IS NULL OR TRY_CONVERT(TIME, end_time) IS NULL THEN 0
                ELSE 
                    DATEDIFF(
                        MINUTE,
                        CAST(TRY_CONVERT(TIME, start_time) AS DATETIME),
                        CASE 
                            WHEN TRY_CONVERT(TIME, end_time) < TRY_CONVERT(TIME, start_time)
                                 THEN DATEADD(DAY, 1, CAST(TRY_CONVERT(TIME, end_time) AS DATETIME))
                            ELSE CAST(TRY_CONVERT(TIME, end_time) AS DATETIME)
                        END
                    ) / 60.0
            END AS ot_hours,
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


def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT department
        FROM OT_Request
        WHERE department IS NOT NULL AND LTRIM(RTRIM(department)) <> ''
        ORDER BY department
    """)
    rows = [r[0] for r in cursor.fetchall()]
    conn.close()
    return rows


def get_employees():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT employee_code, employee_name
        FROM OT_Request
        WHERE employee_code IS NOT NULL AND employee_name IS NOT NULL
        ORDER BY employee_code
    """)
    rows = [(r[0], r[1]) for r in cursor.fetchall()]
    conn.close()
    return rows
