import oracledb

connection = oracledb.connect(
    user="SYSTEM",
    password="lock",
    dsn="localhost/XEPDB1"
)

print("✅ Sikeres kapcsolódás Oracle-hez!")
connection.close()