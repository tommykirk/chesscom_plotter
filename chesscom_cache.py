import sqlite3
import json


class GameCache:
    def __init__(self, db_name=":memory:"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kv_store (
                username TEXT,
                month TEXT,
                value TEXT,
                PRIMARY KEY (username, month)
            )
        ''')
        self.conn.commit()

    def set(self, username, month, value):
        value_json = json.dumps(value)
        self.cursor.execute('''
            INSERT INTO kv_store (username, month, value)
            VALUES (?, ?, ?)
            ON CONFLICT(username, month) DO UPDATE SET value=excluded.value
        ''', (username, month, value_json))
        self.conn.commit()

    def get(self, username, month):
        self.cursor.execute('''
            SELECT value FROM kv_store WHERE username=? AND month=?
        ''', (username, month))
        row = self.cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

    def delete(self, username, month):
        self.cursor.execute('''
            DELETE FROM kv_store WHERE username=? AND month=?
        ''', (username, month))
        self.conn.commit()

    def close(self):
        self.conn.close()


# Example usage:
if __name__ == "__main__":
    db = GameCache()
    db.set("name", "month", {"first": "John", "last": "Doe"})
    print(db.get("name", "month"))  # Output: {'first': 'John', 'last': 'Doe'}
    db.delete("name", "month")
    print(db.get("name", "month"))  # Output: None
    db.close()
