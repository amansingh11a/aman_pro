import json, os
import jwt
import bcrypt
import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import SECRET_KEY, JWT_EXPIRY_HOURS
from db import get_conn, to_dict, to_dicts, _fix_sql, DB_TYPE

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'), static_url_path='')
CORS(app)

@app.route('/')
def index():
    return app.send_static_file('index.html')

# ─── Auth ───────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token missing'}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user_id = data['user_id']
        except:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    body = request.get_json()
    email = body.get('email', '').strip().lower()
    password = body.get('password', '')
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_fix_sql("SELECT id, email, password FROM users WHERE email = %s"), (email,))
    user = to_dict(cur.fetchone())
    cur.close()
    conn.close()
    if not user or not bcrypt.checkpw(password.encode(), user['password'].encode()):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS)
    }, SECRET_KEY, algorithm='HS256')
    return jsonify({'token': token, 'email': user['email']})

@app.route('/api/verify', methods=['GET'])
@token_required
def verify():
    return jsonify({'ok': True})

# ─── Helper ─────────────────────────────────────────────────
def fetch_one(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_fix_sql(sql), params or ())
    row = cur.fetchone()
    cur.close()
    conn.close()
    return to_dict(row)

def fetch_all(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_fix_sql(sql), params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return to_dicts(rows)

def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(_fix_sql(sql), params or ())
    conn.commit()
    lid = cur.lastrowid
    cur.close()
    conn.close()
    return lid

def execute_many(sql, params_list):
    conn = get_conn()
    cur = conn.cursor()
    for params in params_list:
        cur.execute(_fix_sql(sql), params)
    conn.commit()
    cur.close()
    conn.close()

# ─── Hero ───────────────────────────────────────────────────
@app.route('/api/hero', methods=['GET', 'PUT'])
def hero():
    if request.method == 'GET':
        row = fetch_one("SELECT * FROM hero WHERE id = 1")
        if not row:
            return jsonify({})
        return jsonify({
            'tag': row['tag'], 'name_first': row['name_first'], 'name_last': row['name_last'],
            'subtitle': row['subtitle'], 'btn1_text': row['btn1_text'], 'btn1_link': row['btn1_link'],
            'btn2_text': row['btn2_text'], 'btn2_link': row['btn2_link'], 'gold_label': row['gold_label'],
            'hero_img': row['hero_img']
        })
    else:
        @token_required
        def update():
            d = request.get_json()
            conn = get_conn()
            cur = conn.cursor()
            vals = (d.get('tag'), d.get('name_first'), d.get('name_last'), d.get('subtitle'),
                    d.get('btn1_text'), d.get('btn1_link'), d.get('btn2_text'), d.get('btn2_link'),
                    d.get('gold_label'), d.get('hero_img'))
            cur.execute(_fix_sql("UPDATE hero SET tag=%s, name_first=%s, name_last=%s, subtitle=%s, btn1_text=%s, btn1_link=%s, btn2_text=%s, btn2_link=%s, gold_label=%s, hero_img=%s WHERE id=1"), vals)
            if cur.rowcount == 0:
                cur.execute(_fix_sql("INSERT INTO hero (id, tag, name_first, name_last, subtitle, btn1_text, btn1_link, btn2_text, btn2_link, gold_label, hero_img) VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"), vals)
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'ok': True})
        return update()

# ─── About ──────────────────────────────────────────────────
@app.route('/api/about', methods=['GET'])
def get_about():
    paragraphs = [r['paragraph'] for r in fetch_all("SELECT paragraph FROM about_text ORDER BY sort_order")]
    stats = [{'number': r['stat_number'], 'label': r['stat_label']} for r in fetch_all("SELECT stat_number, stat_label FROM stats ORDER BY sort_order")]
    info = [{'label': r['info_label'], 'value': r['info_value']} for r in fetch_all("SELECT info_label, info_value FROM personal_info ORDER BY sort_order")]
    return jsonify({'paragraphs': paragraphs, 'stats': stats, 'info': info})

@app.route('/api/about/paragraphs', methods=['PUT'])
@token_required
def update_paragraphs():
    d = request.get_json()
    execute("DELETE FROM about_text")
    for i, p in enumerate(d.get('paragraphs', [])):
        execute("INSERT INTO about_text (paragraph, sort_order) VALUES (%s, %s)", (p, i))
    return jsonify({'ok': True})

@app.route('/api/about/stats', methods=['PUT'])
@token_required
def update_stats():
    d = request.get_json()
    execute("DELETE FROM stats")
    for i, s in enumerate(d.get('stats', [])):
        execute("INSERT INTO stats (stat_number, stat_label, sort_order) VALUES (%s, %s, %s)", (s.get('number'), s.get('label'), i))
    return jsonify({'ok': True})

@app.route('/api/about/info', methods=['PUT'])
@token_required
def update_info():
    d = request.get_json()
    execute("DELETE FROM personal_info")
    for i, s in enumerate(d.get('info', [])):
        execute("INSERT INTO personal_info (info_label, info_value, sort_order) VALUES (%s, %s, %s)", (s.get('label'), s.get('value'), i))
    return jsonify({'ok': True})

# ─── Skills ─────────────────────────────────────────────────
@app.route('/api/skills', methods=['GET', 'PUT'])
def skills():
    if request.method == 'GET':
        rows = fetch_all("SELECT id, category FROM skills ORDER BY sort_order")
        result = []
        for row in rows:
            tags = [r['tag'] for r in fetch_all("SELECT tag FROM skill_tags WHERE skill_id = %s ORDER BY sort_order", (row['id'],))]
            result.append({'category': row['category'], 'tags': tags})
        return jsonify(result)
    else:
        @token_required
        def update():
            d = request.get_json()
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM skill_tags")
            cur.execute("DELETE FROM skills")
            for i, s in enumerate(d):
                cur.execute("INSERT INTO skills (category, sort_order) VALUES (%s, %s)", (s.get('category'), i))
                sid = cur.lastrowid
                for j, t in enumerate(s.get('tags', [])):
                    cur.execute("INSERT INTO skill_tags (skill_id, tag, sort_order) VALUES (%s, %s, %s)", (sid, t, j))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'ok': True})
        return update()

# ─── Experience ─────────────────────────────────────────────
@app.route('/api/experience', methods=['GET', 'PUT'])
def experience():
    if request.method == 'GET':
        rows = fetch_all("SELECT id, period, role, organization FROM experience ORDER BY sort_order")
        result = []
        for row in rows:
            bullets = [r['bullet'] for r in fetch_all("SELECT bullet FROM exp_bullets WHERE experience_id = %s ORDER BY sort_order", (row['id'],))]
            result.append({'period': row['period'], 'role': row['role'], 'organization': row['organization'], 'bullets': bullets})
        return jsonify(result)
    else:
        @token_required
        def update():
            d = request.get_json()
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM exp_bullets")
            cur.execute("DELETE FROM experience")
            for i, e in enumerate(d):
                cur.execute("INSERT INTO experience (period, role, organization, sort_order) VALUES (%s, %s, %s, %s)",
                        (e.get('period'), e.get('role'), e.get('organization'), i))
                eid = cur.lastrowid
                for j, b in enumerate(e.get('bullets', [])):
                    cur.execute("INSERT INTO exp_bullets (experience_id, bullet, sort_order) VALUES (%s, %s, %s)", (eid, b, j))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'ok': True})
        return update()

# ─── Education ──────────────────────────────────────────────
@app.route('/api/education', methods=['GET', 'PUT'])
def education():
    if request.method == 'GET':
        rows = fetch_all("SELECT year, institution, degree, score FROM education ORDER BY sort_order")
        return jsonify([{'year': r['year'], 'institution': r['institution'], 'degree': r['degree'], 'score': r['score']} for r in rows])
    else:
        @token_required
        def update():
            d = request.get_json()
            execute("DELETE FROM education")
            for i, e in enumerate(d):
                execute("INSERT INTO education (year, institution, degree, score, sort_order) VALUES (%s, %s, %s, %s, %s)",
                        (e.get('year'), e.get('institution'), e.get('degree'), e.get('score'), i))
            return jsonify({'ok': True})
        return update()

# ─── Projects ───────────────────────────────────────────────
@app.route('/api/projects', methods=['GET', 'PUT'])
def projects():
    if request.method == 'GET':
        rows = fetch_all("SELECT id, project_num, title FROM projects ORDER BY sort_order")
        result = []
        for row in rows:
            features = [r['feature'] for r in fetch_all("SELECT feature FROM project_features WHERE project_id = %s ORDER BY sort_order", (row['id'],))]
            result.append({'num': row['project_num'], 'title': row['title'], 'features': features})
        return jsonify(result)
    else:
        @token_required
        def update():
            d = request.get_json()
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM project_features")
            cur.execute("DELETE FROM projects")
            for i, p in enumerate(d):
                cur.execute("INSERT INTO projects (project_num, title, sort_order) VALUES (%s, %s, %s)", (p.get('num'), p.get('title'), i))
                pid = cur.lastrowid
                for j, f in enumerate(p.get('features', [])):
                    cur.execute("INSERT INTO project_features (project_id, feature, sort_order) VALUES (%s, %s, %s)", (pid, f, j))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'ok': True})
        return update()

# ─── Awards ─────────────────────────────────────────────────
@app.route('/api/awards', methods=['GET', 'PUT'])
def awards():
    if request.method == 'GET':
        rows = fetch_all("SELECT title, description FROM awards ORDER BY sort_order")
        return jsonify([{'title': r['title'], 'description': r['description']} for r in rows])
    else:
        @token_required
        def update():
            d = request.get_json()
            execute("DELETE FROM awards")
            for i, a in enumerate(d):
                execute("INSERT INTO awards (title, description, sort_order) VALUES (%s, %s, %s)", (a.get('title'), a.get('description'), i))
            return jsonify({'ok': True})
        return update()

# ─── Contact ────────────────────────────────────────────────
@app.route('/api/contact', methods=['GET', 'PUT'])
def contact():
    if request.method == 'GET':
        row = fetch_one("SELECT * FROM contact WHERE id = 1")
        if not row:
            return jsonify({})
        return jsonify({
            'email': row['email'], 'phone': row['phone'], 'whatsapp_link': row['whatsapp_link'],
            'linkedin_url': row['linkedin_url'], 'linkedin_text': row['linkedin_text'],
            'location': row['location'], 'message_text': row['message_text']
        })
    else:
        @token_required
        def update():
            d = request.get_json()
            conn = get_conn()
            cur = conn.cursor()
            vals = (d.get('email'), d.get('phone'), d.get('whatsapp_link'),
                    d.get('linkedin_url'), d.get('linkedin_text'),
                    d.get('location'), d.get('message_text'))
            cur.execute(_fix_sql("UPDATE contact SET email=%s, phone=%s, whatsapp_link=%s, linkedin_url=%s, linkedin_text=%s, location=%s, message_text=%s WHERE id=1"), vals)
            if cur.rowcount == 0:
                cur.execute(_fix_sql("INSERT INTO contact (id, email, phone, whatsapp_link, linkedin_url, linkedin_text, location, message_text) VALUES (1, %s, %s, %s, %s, %s, %s, %s)"), vals)
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'ok': True})
        return update()

# ─── Export ─────────────────────────────────────────────────
@app.route('/api/export', methods=['GET'])
@token_required
def export_all():
    h = fetch_one("SELECT * FROM hero WHERE id = 1")
    hero_data = {
        'tag': h['tag'], 'name_first': h['name_first'], 'name_last': h['name_last'],
        'subtitle': h['subtitle'], 'btn1_text': h['btn1_text'], 'btn1_link': h['btn1_link'],
        'btn2_text': h['btn2_text'], 'btn2_link': h['btn2_link'], 'gold_label': h['gold_label'],
        'hero_img': h['hero_img']
    } if h else {}

    paragraphs = [r['paragraph'] for r in fetch_all("SELECT paragraph FROM about_text ORDER BY sort_order")]
    stats = [{'number': r['stat_number'], 'label': r['stat_label']} for r in fetch_all("SELECT stat_number, stat_label FROM stats ORDER BY sort_order")]
    info = [{'label': r['info_label'], 'value': r['info_value']} for r in fetch_all("SELECT info_label, info_value FROM personal_info ORDER BY sort_order")]

    skills = []
    for row in fetch_all("SELECT id, category FROM skills ORDER BY sort_order"):
        tags = [r['tag'] for r in fetch_all("SELECT tag FROM skill_tags WHERE skill_id = %s ORDER BY sort_order", (row['id'],))]
        skills.append({'category': row['category'], 'tags': tags})

    experience = []
    for row in fetch_all("SELECT id, period, role, organization FROM experience ORDER BY sort_order"):
        bullets = [r['bullet'] for r in fetch_all("SELECT bullet FROM exp_bullets WHERE experience_id = %s ORDER BY sort_order", (row['id'],))]
        experience.append({'period': row['period'], 'role': row['role'], 'organization': row['organization'], 'bullets': bullets})

    education = [{'year': r['year'], 'institution': r['institution'], 'degree': r['degree'], 'score': r['score']} for r in fetch_all("SELECT year, institution, degree, score FROM education ORDER BY sort_order")]

    projects = []
    for row in fetch_all("SELECT id, project_num, title FROM projects ORDER BY sort_order"):
        features = [r['feature'] for r in fetch_all("SELECT feature FROM project_features WHERE project_id = %s ORDER BY sort_order", (row['id'],))]
        projects.append({'num': row['project_num'], 'title': row['title'], 'features': features})

    awards = [{'title': r['title'], 'description': r['description']} for r in fetch_all("SELECT title, description FROM awards ORDER BY sort_order")]

    c = fetch_one("SELECT * FROM contact WHERE id = 1")
    contact_data = {
        'email': c['email'], 'phone': c['phone'], 'whatsapp_link': c['whatsapp_link'],
        'linkedin_url': c['linkedin_url'], 'linkedin_text': c['linkedin_text'],
        'location': c['location'], 'message_text': c['message_text']
    } if c else {}

    return jsonify({
        'hero': hero_data, 'paragraphs': paragraphs, 'stats': stats, 'info': info,
        'skills': skills, 'experience': experience, 'education': education,
        'projects': projects, 'awards': awards, 'contact': contact_data
    })

# Auto-create tables & seed on startup
with app.app_context():
    try:
        from database import create_tables, seed_admin
        create_tables()
        seed_admin()
        if DB_TYPE == 'sqlite':
            seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed.json')
            if os.path.exists(seed_path):
                row = fetch_one("SELECT COUNT(*) AS c FROM hero")
                if row['c'] == 0:
                    print('[INFO] Loading seed data...')
                    from db_seed import load_seed
                    load_seed(seed_path)
    except Exception as e:
        print('[WARN] DB setup error:', e)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
