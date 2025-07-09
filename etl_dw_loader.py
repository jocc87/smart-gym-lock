import psycopg2
import pandas as pd
from datetime import datetime

# ==== ETL: Extract - Transform - Load ====

# --- Kapcsolódási adatok (PostgreSQL)
db_params = {
    "dbname": "gym",
    "user": "postgres",
    "password": "postgres123",
    "host": "localhost",
    "port": "5432"
}

# --- PostgreSQL kapcsolat létrehozása
def get_conn():
    return psycopg2.connect(**db_params)

# === 1. EXTRACT ===
def extract_logs():
    conn = get_conn()
    query = """
        SELECT user_id, lock_date
        FROM logs
        WHERE success = TRUE
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# === 2. TRANSFORM ===
def transform_logs(df):
    df['lock_date'] = pd.to_datetime(df['lock_date'])
    df['date'] = df['lock_date'].dt.date
    df['hour'] = df['lock_date'].dt.hour

    # Napi összesítés felhasználónként
    daily_stats = df.groupby(['date', 'user_id']).agg(
        access_count=('user_id', 'count'),
        first_access=('lock_date', 'min'),
        last_access=('lock_date', 'max')
    ).reset_index()

    # Óránkénti nyitások összesen (peak hours)
    hourly_stats = df.groupby('hour').agg(
        total_access=('user_id', 'count')
    ).reset_index().rename(columns={'hour': 'access_hour'})

    return daily_stats, hourly_stats

# === 3. LOAD ===
def load_dw_tables(daily_stats, hourly_stats):
    conn = get_conn()
    cur = conn.cursor()

    # Napi stat betöltés
    for _, row in daily_stats.iterrows():
        cur.execute("""
            INSERT INTO dw_access_stats (stat_date, user_id, access_count, first_access, last_access)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (stat_date, user_id) DO UPDATE SET
                access_count = EXCLUDED.access_count,
                first_access = EXCLUDED.first_access,
                last_access = EXCLUDED.last_access;
        """, (row['date'], row['user_id'], row['access_count'], row['first_access'], row['last_access']))

    # Óránkénti stat betöltés
    for _, row in hourly_stats.iterrows():
        cur.execute("""
            INSERT INTO dw_peak_hours (access_hour, total_access)
            VALUES (%s, %s)
            ON CONFLICT (access_hour) DO UPDATE SET
                total_access = EXCLUDED.total_access;
        """, (int(row['access_hour']), int(row['total_access'])))

    conn.commit()
    cur.close()
    conn.close()

# === MAIN ===
if __name__ == "__main__":
    print("🔄 ETL folyamat indul...", datetime.now())

    logs_df = extract_logs()
    print(f"✅ {len(logs_df)} sikeres log beolvasva")

    daily_stats, hourly_stats = transform_logs(logs_df)
    print(f"📊 {len(daily_stats)} napi rekord, {len(hourly_stats)} órás rekord generálva")

    load_dw_tables(daily_stats, hourly_stats)
    print("✅ Betöltés kész: adattárház frissítve")
