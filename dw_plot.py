import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.ticker as mticker

db_params = {
    "dbname": "gym",
    "user": "postgres",
    "password": "postgres123",
    "host": "localhost",
    "port": "5432"
}

def get_conn():
    return psycopg2.connect(**db_params)

# === 1. Napi statisztika: top userek ===
def plot_top_users():
    conn = get_conn()
    query = """
        SELECT u.name, SUM(d.access_count) as total
        FROM dw_access_stats d
        JOIN users u ON d.user_id = u.id
        WHERE stat_date >= %s
        GROUP BY u.name
        ORDER BY total DESC
        LIMIT 10;
    """
    start_date = (datetime.today() - timedelta(days=30)).date()
    df = pd.read_sql(query, conn, params=(start_date,))
    conn.close()

    plt.figure()
    plt.bar(df['name'], df['total'])
    plt.title("Top 10 felhasználó (elmúlt 30 nap)")
    plt.xticks(rotation=45)
    plt.xlabel("Felhasználó")
    plt.ylabel("Nyitások száma")
    plt.tight_layout()
    plt.savefig("static/top_users.png")
    print("📊 Mentve: top_users.png")

# === 2. Csúcsidő: óránkénti nyitások ===
def plot_peak_hours():
    conn = get_conn()
    query = """
        SELECT access_hour, total_access
        FROM dw_peak_hours
        ORDER BY access_hour;
    """
    df = pd.read_sql(query, conn)
    conn.close()

    plt.figure()
    plt.plot(df['access_hour'], df['total_access'], marker='o')
    plt.title("Csúcsidő: óránkénti nyitások")
    plt.xlabel("Óra")
    plt.ylabel("Nyitások száma")
    plt.xticks(range(0, 24))
    plt.grid(True)
    plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.savefig("static/peak_hours.png")
    print("📊 Mentve: peak_hours.png")

# === MAIN ===
if __name__ == "__main__":
    plot_top_users()
    plot_peak_hours()
