import json, bcrypt
from db import get_conn

TABLES_TO_SEED = [
    ('users', 'id'),
    ('hero', 'id'),
    ('about_text', 'id'),
    ('stats', 'id'),
    ('personal_info', 'id'),
    ('skills', 'id'),
    ('skill_tags', 'id'),
    ('experience', 'id'),
    ('exp_bullets', 'id'),
    ('education', 'id'),
    ('projects', 'id'),
    ('project_features', 'id'),
    ('awards', 'id'),
    ('contact', 'id'),
]

def load_seed(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    conn = get_conn()
    cur = conn.cursor()
    for table, pk in TABLES_TO_SEED:
        rows = data.get(table, [])
        if not rows:
            continue
        cur.execute(f"DELETE FROM {table}")
        for row in rows:
            cols = list(row.keys())
            placeholders = ','.join(['?'] * len(cols))
            values = [row[k] for k in cols]
            if table == 'users' and 'password' in cols:
                idx = cols.index('password')
                pwd = values[idx]
                if not pwd.startswith('$2b$'):
                    values[idx] = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
            cur.execute(sql, values)
    conn.commit()
    cur.close()
    conn.close()
    print(f'[OK] Loaded seed data from {path}')
