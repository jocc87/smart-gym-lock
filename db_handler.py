import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import config 
import bcrypt

def hash_password(raw_password):
    if not raw_password:
        return None
    return bcrypt.hashpw(str(raw_password).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

class DBHandler:
    def __init__(self, dbname="gym", user="postgres", password="postgres123", host="localhost", port="5432"):
        self.conn_params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def insert_right_for_passcode(self, user_id: int, passcode: str,
                                  valid_from: datetime, valid_until: datetime) -> bool:
        """
        Beszúr egy új jogot ('passcode') adott userhez.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO rights
                  (user_id, lock_id, access_type, access_value, valid_from, valid_until)
                VALUES (%s, %s, 'passcode', %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                user_id,
                config.LOCK_ID,
                passcode,
                valid_from,
                valid_until
            ))
            conn.commit()
            return True
        except Exception as e:
            print("❌ Hiba rights beszúrásakor:", e)
            return False
        finally:
            cur.close()
            conn.close()

    def insert_lock(self, location):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO locks (location) VALUES (%s);", (location,))
        conn.commit()
        cur.close()
        conn.close()

    def get_locks(self):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM locks;")
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    
    def get_latest_log_timestamp(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT MAX(lock_date) FROM logs;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return int(result[0].timestamp() * 1000) if result and result[0] else 0

    def insert_log_from_record(self, record):
        conn = self.get_connection()
        cur = conn.cursor()
    
        try:
            # Megnézzük, benne van-e már a rekord
            cur.execute("SELECT 1 FROM logs WHERE record_id = %s", (record["recordId"],))
            if cur.fetchone():
                # már létezik, kihagyjuk
                return False
    
            # Átalakítás
            lock_date = datetime.fromtimestamp(record["lockDate"] / 1000)
    
            # Lock ID lekérése
            cur.execute("SELECT id FROM locks WHERE id = %s", (record["lockId"],))
            result = cur.fetchone()
            lock_id = result[0] if result else None
            if lock_id is None:
                print("⚠️ Ismeretlen lockId:", record["lockId"])
                return False
    
            # User ID keresés
            cur.execute("SELECT id FROM users WHERE name = %s", (record["username"],))
            result = cur.fetchone()
            user_id = result[0] if result else None
    
            # Beszúrás
            cur.execute("""
                INSERT INTO logs (
                    record_id, user_id, lock_id, username, keyboard_pwd,
                    record_type, lock_date, success
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                record["recordId"],
                user_id,
                lock_id,
                record["username"],
                record["keyboardPwd"],
                record["recordType"],
                lock_date,
                bool(record["success"])
            ))
    
            conn.commit()
            return True
    
        except Exception as e:
            print("❌ Hiba rekord beszúrásakor:", e)
            return False
    
        finally:
            cur.close()
            conn.close()
    
    def search_user(self, username, email, passcode = 0):
        conn = self.get_connection()
        cur = conn.cursor()

        try:
           password_hash = hash_password(passcode)
           conn = self.get_connection()
           cur = conn.cursor()
           # USER létrehozás vagy keresés
           cur.execute("SELECT id FROM users WHERE name = %s", (username,))
           result = cur.fetchone()
           if result:
               user_id = result[0]
           else:
               cur.execute(
                   "INSERT INTO users (name, email, password_hash, passcode) VALUES (%s, %s, %s, %s) RETURNING id;",
                   (username, email, password_hash if passcode != 0 else None, passcode if passcode != 0 else None)
               )
               user_id = cur.fetchone()[0]
               conn.commit() 
           return user_id
    
        except Exception as e:
            print("❌ Hiba user létrehozásnál:", e)
            return None
        finally:
            cur.close()
            conn.close()

    def insert_user_and_right_from_passcode(self, record):
        conn = self.get_connection()
        cur = conn.cursor()
    
        try:
            username = record.get("keyboardPwdName")
            if not username:
                return False
    
            # email alapból
            email = f"{username}@placeholder.local"
            passcode = record.get("keyboardPwd")
    
            user_id = self.search_user(username, email, passcode)
    
            # RIGHT beszúrás
            valid_from = datetime.fromtimestamp(record.get("startDate", 0) / 1000) if record.get("startDate") else None
            valid_until = datetime.fromtimestamp(record.get("endDate", 0) / 1000) if record.get("endDate") else None
    
            cur.execute("""
                INSERT INTO rights (
                    user_id, lock_id, access_type, access_value, valid_from, valid_until
                ) VALUES (%s, %s, 'passcode', %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (user_id, config.LOCK_ID, passcode, valid_from, valid_until))
    
            conn.commit()
            return True

        except Exception as e:
            print("❌ Hiba passcode beszúrásakor:", e)
            return False
        finally:
             cur.close()
             conn.close()

    def insert_user_and_right_from_fingerprint(self, record):
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            username = record.get("fingerprintName") or f"fingerprint_{record.get('fingerprintId', 'unknown')}"
            email = f"{username}@placeholder.local"
            fingerprint_id = str(record.get("fingerprintId"))
            print("➡️ username:", username)
            user_id = self.search_user(username, email)

            # RIGHT beszúrás
            valid_from = datetime.fromtimestamp(record.get("startDate", 0) / 1000) if record.get("startDate") else None
            valid_until = datetime.fromtimestamp(record.get("endDate", 0) / 1000) if record.get("endDate") else None

            cur.execute("""
                INSERT INTO rights (
                    user_id, lock_id, access_type, access_value, valid_from, valid_until
                ) VALUES (%s, %s, 'fingerprint', %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (user_id, config.LOCK_ID, fingerprint_id, valid_from, valid_until))

            conn.commit()
            return True

        except Exception as e:
            print("❌ Hiba fingerprint beszúrásakor:", e)
            return False
        finally:
            cur.close()
            conn.close()

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


    def create_order(self, username: str, passcode: str, amount: int = 5000) -> int | None:
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            # user ID lekérdezés
            cur.execute("SELECT id FROM users WHERE name = %s AND passcode = %s", (username, passcode))
            user = cur.fetchone()
            if not user:
                print(f"❌ Nincs ilyen user vagy passcode: {username}{passcode}")
                return None

            user_id = user[0]

            # rendelés beszúrása (a trigger automatikusan jogot generál)
            cur.execute("""
                INSERT INTO orders (user_id, passcode, amount, status)
                VALUES (%s, %s, %s, 'paid')
                RETURNING id;
            """, (user_id, passcode, amount))
            order_id = cur.fetchone()[0]
            conn.commit()
            return order_id

        except Exception as e:
            print("❌ Hiba rendelés létrehozásakor:", e)
            return None
        finally:
            cur.close()
            conn.close()

    def get_user_stats(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT * FROM user_open_stats();")
            rows = cur.fetchall()

            stats = []
            for row in rows:
                stats.append({
                    "username": row[0],
                    "nyitasok": row[1],
                    "sikeres": row[2],
                    "sikertelen": row[3]
                })
            return stats

        except Exception as e:
            print("❌ Hiba statisztika lekérdezésekor:", e)
            return []
        finally:
            cur.close()
            conn.close()
