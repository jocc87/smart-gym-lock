from api_handler import APIHandler
from db_handler import DBHandler
from datetime import datetime
import subprocess

api = APIHandler()
db = DBHandler()

print("🔄 Indul a log szinkron:", datetime.now())

try:
    # 1. Legutóbbi log időpont lekérdezése
    last_ts = db.get_latest_log_timestamp()
    print("➡️ Utolsó ismert időbélyeg:", last_ts)

    # 2. Új logok lekérése API-ból
    new_logs = api.get_lockRecords_since(last_ts)

    # 3. Beszúrás DB-be
    count = 0
    for log in new_logs:
        if db.insert_log_from_record(log):
            count += 1

    print(f"✅ {count} új log betöltve.")

    # 🚀 Ha volt új adat, indítsuk az ETL scriptet
    if count > 0:
        print("📦 Új adatok érkeztek – ETL indul...")
        subprocess.run(["python", "etl_dw_loader.py"])
    else:
        print("📦 Nem érkezett új adat – ETL kihagyva.")

    # 4. Naplózás a sync_log táblába
    db_conn = db.get_connection()
    cur = db_conn.cursor()
    cur.execute("""
        INSERT INTO sync_log (sync_time, new_records, success, error)
        VALUES (NOW(), %s, %s, %s);
    """, (count, True, None))
    db_conn.commit()
    cur.close()
    db_conn.close()

except Exception as e:
    print("❌ Hiba szinkron közben:", e)

    # 5. Hibás eset naplózása
    try:
        db_conn = db.get_connection()
        cur = db_conn.cursor()
        cur.execute("""
            INSERT INTO sync_log (sync_time, new_records, success, error)
            VALUES (NOW(), %s, %s, %s);
        """, (0, False, str(e)))
        db_conn.commit()
        cur.close()
        db_conn.close()
    except Exception as inner:
        print("‼️ Hiba a hibanaplózáskor is:", inner)