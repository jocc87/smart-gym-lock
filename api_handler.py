import requests
import hashlib
import time
from datetime import datetime, timedelta
import config 

class APIHandler:
    def __init__(self):
        self.access_token = None
        self.token_expires_at = 0  # UNIX timestamp (lejárati idő)
    
    # api_handler.py
import requests
from datetime import datetime
import config

class APIHandler:
    def get_keyboard_pwd_id_by_passcode(self, passcode: str) -> int | None:
        all_pwds = self.get_passcodes()
        for rec in all_pwds:
            if rec.get("keyboardPwd") == passcode:
                return rec.get("keyboardPwdId")
        return None


    def update_passcode(self, keyboardPwdId: int, valid_from: datetime = datetime.now(), 
                        valid_until: datetime = datetime.now() + timedelta(days=30)):
        """
        Módosítja a meglévő passcode időablakát a zárban.
        """
        payload = {
            "clientId":     config.CLIENT_ID,
            "accessToken":  config.TOKEN,
            "lockId":       config.LOCK_ID,
            "keyboardPwdId": keyboardPwdId,
            "startDate":    int(valid_from.timestamp() * 1000),   # ms-ben
            "endDate":      int(valid_until.timestamp() * 1000),  # ms-ben
            "date":         int(datetime.now().timestamp() * 1000),
            "changeType":   2
        }
        resp = requests.post(config.SET_PASSCODE, data=payload)
        result = resp.json()
        if result.get("errcode") != 0:
            raise RuntimeError(f"TTLock API hiba: {result}")
        return result


    def get_access_token(self, username, password):
        encrypted_password = hashlib.md5(password.encode()).hexdigest()

        data = {
            "clientId": config.CLIENT_ID,
            "clientSecret": config.CLIENT_SECRET,
            "username": username,
            "password": encrypted_password,
            "grant_type": "password"
        }

        response = requests.post(config.TOKEN_URL, data=data)

        try:
            result = response.json()
        except Exception as e:
            print("❌ JSON parse error a token kérésnél:", e)
            print("🔴 RAW válasz a szervertől:")
            print(response.text)
            return {}

        if "access_token" in result:
            self.access_token = result["access_token"]
            self.token_expires_at = int(time.time()) + result.get("expires_in", 86400)
            print("🔐 Új token:", self.access_token)
        else:
            print("⚠️ Token nem jött vissza:", result)

        return result


    def get_passcodes(self):
       all_passcodes = []

       for page in range(1, 2):
           params = {
               "clientId": config.CLIENT_ID,
               "accessToken": config.TOKEN,
               "lockId": config.LOCK_ID,
               "pageNo": page,
               "pageSize": 100,
               "date": int(datetime.now().timestamp() * 1000)
           }

           response = requests.get(config.PASSCODE_LIST_URL, params=params)

           try:
               data = response.json()
           except Exception as e:
               print("❌ JSON parse error a passcode lekérdezésnél:", e)
               print("RAW response:", response.text)
               break

           if not data.get("list"):
               break

           all_passcodes.extend(data["list"])

       return all_passcodes

    
    def get_fingerprints(self):
        all_data = []

        for page in range(1, 2):
            params = {
                "clientId": config.CLIENT_ID,
                "accessToken": config.TOKEN,
                "lockId": config.LOCK_ID,
                "pageNo": page,
                "pageSize": 100,
                "date": int(datetime.now().timestamp() * 1000)
            }

            response = requests.get(config.FP_LIST_URL, params=params)
            try:
                data = response.json()
            except Exception as e:
                print("❌ JSON parsing error:", e)
                return []

            if not data.get("list"):
                break

            all_data.extend(data["list"])

        return all_data
    
    def get_lockRecords(self):
        all_records = []

        for page in range(1, 16):  # 1-től 15-ig
            params = {
                "clientId": config.CLIENT_ID,
                "accessToken": config.TOKEN,
                "lockId": config.LOCK_ID,
                "pageNo": page,
                "pageSize": 100,
                "date": int(datetime.now().timestamp() * 1000)
            }

            response = requests.get(config.LOCK_REC, params=params)
            data = response.json()

            if data.get("list"):
                all_records.extend(data["list"])
            else:
                break  

        return all_records

    def get_lockRecords_since(self, start_timestamp):
        all_records = []

        for page in range(1, 16):  # max 1500 rekord
            params = {
                "clientId": config.CLIENT_ID,
                "accessToken": config.TOKEN,
                "lockId": config.LOCK_ID,
                "pageNo": page,
                "pageSize": 100,
                "startDate": start_timestamp,
                "endDate": 0,  # 0 = nincs felső korlát
                "date": int(datetime.now().timestamp() * 1000)
            }

            response = requests.get(config.LOCK_REC, params=params)
            data = response.json()
            if not data.get("list"):
                break

            all_records.extend(data["list"])

        return all_records

if __name__ == "__main__":
    handler = APIHandler()
    result = handler.get_access_token(config.USERNAME, config.PASSWORD)
    print(result)
