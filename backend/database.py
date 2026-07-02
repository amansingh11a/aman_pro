import bcrypt
from db import get_conn, DB_TYPE, _fix_sql

def _pk():
    return "INTEGER PRIMARY KEY AUTOINCREMENT" if DB_TYPE == 'sqlite' else "INT AUTO_INCREMENT PRIMARY KEY"

def _col(t):
    if DB_TYPE == 'sqlite':
        t = t.replace('VARCHAR(255)', 'TEXT').replace('VARCHAR(100)', 'TEXT').replace('VARCHAR(50)', 'TEXT').replace('VARCHAR(10)', 'TEXT').replace('VARCHAR(20)', 'TEXT')
    return t

def _ie(sql):
    return _fix_sql(sql) if DB_TYPE == 'sqlite' else sql

def create_tables():
    conn = get_conn()
    cur = conn.cursor()
    pk = _pk()
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS users (
          id {pk},
          email TEXT NOT NULL UNIQUE,
          password TEXT NOT NULL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS hero (
          id {pk},
          tag TEXT, name_first TEXT, name_last TEXT,
          subtitle TEXT, btn1_text TEXT, btn1_link TEXT,
          btn2_text TEXT, btn2_link TEXT, gold_label TEXT, hero_img TEXT
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS about_text (
          id {pk}, paragraph TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS stats (
          id {pk}, stat_number TEXT, stat_label TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS personal_info (
          id {pk}, info_label TEXT, info_value TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS skills (
          id {pk}, category TEXT NOT NULL, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS skill_tags (
          id {pk}, skill_id INT NOT NULL, tag TEXT NOT NULL,
          sort_order INT DEFAULT 0, FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS experience (
          id {pk}, period TEXT, role TEXT,
          organization TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS exp_bullets (
          id {pk}, experience_id INT NOT NULL, bullet TEXT,
          sort_order INT DEFAULT 0, FOREIGN KEY (experience_id) REFERENCES experience(id) ON DELETE CASCADE
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS education (
          id {pk}, year TEXT, institution TEXT,
          degree TEXT, score TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS projects (
          id {pk}, project_num TEXT, title TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS project_features (
          id {pk}, project_id INT NOT NULL, feature TEXT,
          sort_order INT DEFAULT 0, FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS awards (
          id {pk}, title TEXT, description TEXT, sort_order INT DEFAULT 0
        )
    """))
    cur.execute(_ie(f"""
        CREATE TABLE IF NOT EXISTS contact (
          id {pk}, email TEXT, phone TEXT,
          whatsapp_link TEXT, linkedin_url TEXT, linkedin_text TEXT,
          location TEXT, message_text TEXT
        )
    """))
    conn.commit()
    cur.close()
    conn.close()
    print('[OK] Tables created')

def seed_admin():
    conn = get_conn()
    cur = conn.cursor()
    password = bcrypt.hashpw('9236115181'.encode(), bcrypt.gensalt()).decode()
    cur.execute(_fix_sql("SELECT id FROM users WHERE email = %s"), ('amansingh955987@gmail.com',))
    if not cur.fetchone():
        cur.execute(_fix_sql("INSERT INTO users (email, password) VALUES (%s, %s)"), ('amansingh955987@gmail.com', password))
        conn.commit()
        print('[OK] Admin user created (amansingh955987@gmail.com / 9236115181)')
    else:
        cur.execute(_fix_sql("UPDATE users SET password = %s WHERE email = %s"), (password, 'amansingh955987@gmail.com'))
        conn.commit()
        print('[OK] Admin password updated')
    cur.close()
    conn.close()
