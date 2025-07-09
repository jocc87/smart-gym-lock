from flask import Flask, jsonify, request, render_template
from db_handler import DBHandler 
from api_handler import APIHandler 
from datetime import datetime, timedelta
import json 

app = Flask(__name__)
api_handler = APIHandler() 
db_handler = DBHandler()

@app.route('/')
def home():
    return render_template('index.html')

"""-----------------DB functions------------------"""

@app.route("/api/locks", methods=["GET"])
def api_get_locks():
    return jsonify(db_handler.get_locks())



"""----------------api calls----------------------"""

@app.route("/api/passcodes", methods=["GET"])
def api_get_passcodes():
    """API végpont a passcode-ok lekérésére."""
    return jsonify(api_handler.get_passcodes())

@app.route("/api/fingerprints", methods=["GET"])
def api_get_fingerprints():
    try:
        fingerprints = api_handler.get_fingerprints()
        return jsonify(fingerprints)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""legutóbbi frissítés óta történt nyitási logok lekérése"""
@app.route("/api/load_new_logs", methods=["POST"])
def load_new_logs():
    try:
        # Utolsó ismert időpont lekérdezése adatbázisból
        last_ts = db_handler.get_latest_log_timestamp()
        records = api_handler.get_lockRecords_since(last_ts)

        count = 0
        for rec in records:
            ret = db_handler.insert_log_from_record(rec)
            count += 1 if ret else 0

        return jsonify({"message": f"{count} új rekord betöltve."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
     

@app.route("/api/load_logs", methods=["POST"])
def load_logs():
    try:
        records = api_handler.get_lockRecords()  # teljes lekérés, nem szűkített

        count = 0
        for rec in records:
            ret = db_handler.insert_log_from_record(rec)
            count += 1 if ret else 0

        return jsonify({"message": f"{count} rekord betöltve teljes lekérdezéssel."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

"""passcodok, fingerprints szinkronizálása, users és rughts táblába"""    
@app.route("/api/sync_passcodes", methods=["POST"])
def sync_passcode_rights():
    try:
        print("PASSCODE SZINKRON INDUL...")
        passcodes = api_handler.get_passcodes()
        print(f"Rekordok száma: {len(passcodes)}")
        print("Első rekord:", passcodes[0] if passcodes else "NINCS ADAT")

        count = 0

        for rec in passcodes:
            if db_handler.insert_user_and_right_from_passcode(rec):
                count += 1

        return jsonify({"message": f"{count} passcode rekord feldolgozva."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sync_fingerprints", methods=["POST"])
def sync_fingerprint_rights():
    try:
        fingerprints = api_handler.get_fingerprints()
        count = 0

        for rec in fingerprints:
            if db_handler.insert_user_and_right_from_fingerprint(rec):
                count += 1

        return jsonify({"message": f"{count} fingerprint rekord feldolgozva."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_user_id_by_name(self, username: str):
    conn = self.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM users WHERE name = %s", (username,))
        result = cur.fetchone()
        return result[0] if result else None
    finally:
        cur.close()
        conn.close()

@app.route("/api/update_passcode", methods=["POST"])
def api_update_passcode():
    data = request.get_json()
    try:
        passcode = data["passcode"]
        username = data.get("username")  # optional

        # keresd ki a keyboardPwdId-t
        kp_id = api_handler.get_keyboard_pwd_id_by_passcode(passcode)
        if not kp_id:
            return jsonify({"error": "Passcode nem található a záron"}), 404

        # időintervallum
        start_dt = datetime.now()
        end_dt = start_dt + timedelta(days=30)

        # TTLock API hívás
        api_handler.update_passcode(kp_id, start_dt, end_dt)

        # felhasználó ID lekérdezés (akár csak név alapján)
        if not username:
            username = f"user_{passcode}"  # fallback ha nincs név
        user_id = db_handler.get_user_id_by_name(username)
        if not user_id:
            return jsonify({"error": f"User '{username}' nem található"}), 404

        # jog beírása
        db_handler.insert_right_for_passcode(user_id, passcode, start_dt, end_dt)

        return jsonify({
            "message": "Passcode frissítve és jog bejegyezve.",
            "valid_from": start_dt.isoformat(),
            "valid_until": end_dt.isoformat()
        })

    except Exception as e:
        return jsonify({"error": f"Nem várt hiba: {e}"}), 500


@app.route("/api/order", methods=["POST"])
def create_order():
    """
    Bemenet JSON:
    {
        "username": "sara",
        "passcode": "1234",
        "amount": 5000  (opcionális)
    }
    """
    data = request.get_json()

    try:
        username = data["username"]
        passcode = data["passcode"]
        amount = data.get("amount", 5000)

        # beszúrás db_handleren keresztül
        order_id = db_handler.create_order(username, passcode, amount)
        if not order_id:
            return jsonify({"error": "Sikertelen rendelés"}), 500
        
    
        pwd = api_handler.get_keyboard_pwd_id_by_passcode(passcode)
        api_handler.update_passcode(pwd)
        return jsonify({
            "message": "Sikeres rendelés, jogosultság automatikusan létrejön.",
            "order_id": order_id
        })

    except KeyError as ke:
        return jsonify({"error": f"Hiányzó mező: {ke}"}), 400
    except Exception as e:
        return jsonify({"error": f"Nem várt hiba: {e}"}), 500

@app.route("/api/user_stats", methods=["GET"])
def api_user_stats():
    try:
        stats = db_handler.get_user_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug = True, port=5001)
