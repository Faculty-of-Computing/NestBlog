from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db, close_connection, init_db
from functools import wraps
from flask import g
import os
import re
from dotenv import load_dotenv

import secrets
import hashlib
from psycopg2 import IntegrityError
import psycopg2
from psycopg2.extras import RealDictCursor

from datetime import datetime
app = Flask(__name__)
load_dotenv()  
image_dir = os.path.join('static', 'images')
os.makedirs(image_dir, exist_ok=True)

app.secret_key = os.getenv("SECRET_KEY")

# config.py or app.py
app.config['DB_NAME'] = os.getenv("DB_NAME")
app.config['DB_USER'] = os.getenv("DB_USER")
app.config['DB_PASSWORD'] = os.getenv("DB_PASSWORD")
app.config['DB_HOST'] = os.getenv("DB_HOST")
app.config['DB_PORT'] = os.getenv("DB_PORT")


@app.before_request
def set_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)

app.jinja_env.globals['csrf_token'] = lambda: session.get('csrf_token')


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=session.get('csrf_token'))

@app.context_processor
def inject_user():
    db = get_db()
    user = None
    if 'user_id' in session:
        with db.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM "user" WHERE id = %s',
                (session['user_id'],)
            )
            user = cur.fetchone()
    return dict(user=user)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        with db.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM "user" WHERE id = %s', (user_id,))
            g.user = cur.fetchone()

def get_post_by_id(post_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                post.*, 
                category.name AS category_name,
                "user".username AS author_name
            FROM post 
            LEFT JOIN category ON post.category_id = category.id
            LEFT JOIN "user" ON post.user_id = "user".id
            WHERE post.id = %s
        """, (post_id,))
        post = cur.fetchone()
    return post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    db = get_db()
    current_user_id = session.get('user_id')

    with db.cursor(cursor_factory=RealDictCursor) as cur:
        # check if post exists and belongs to current user
        cur.execute("""
            SELECT id, user_id 
            FROM post 
            WHERE id = %s
        """, (post_id,))
        post = cur.fetchone()

        if not post:
            flash("Post not found.", "warning")
            return redirect(url_for('index'))

        if post['user_id'] != current_user_id:
            flash("You are not authorized to delete this post.", "danger")
            return redirect(url_for('index'))

        # delete comments first if no ON DELETE CASCADE
        cur.execute("DELETE FROM comment WHERE post_id = %s", (post_id,))

        # delete the post
        cur.execute("DELETE FROM post WHERE id = %s", (post_id,))

        db.commit()

    flash("Post deleted successfully.", "success")
    return redirect(url_for('index'))

@app.route('/editpost/<int:post_id>', methods=['GET', 'POST'])
@login_required
def editpost(post_id):
    db = get_db()
    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM post WHERE id = %s", (post_id,))
        post = cur.fetchone()
        
    if not post:
        return "Post not found", 404

    if post['user_id'] != session['user_id']:
        return "Unauthorized", 403

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        draft = bool(request.form.get('draft'))
        category_id = request.form.get('category_id')

        featured_image = post['featured_image']
        if 'featured_image' in request.files:
            image = request.files['featured_image']
            if image and image.filename:
                image_path = os.path.join('static/images', image.filename)
                image.save(image_path)
                featured_image = image.filename

        with db.cursor() as cur:
            cur.execute("""
                UPDATE post
                SET title = %s, body = %s, draft = %s, category_id = %s, featured_image = %s
                WHERE id = %s
            """, (title, content, draft, category_id, featured_image, post_id))
            db.commit()

        return redirect(url_for('index'))

    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM category")
        categories = cur.fetchall()
    return render_template('editpost.html', post=post, categories=categories)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # CSRF Validation
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return "CSRF validation failed", 400

        # Form Data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO "user" (username, email, password) VALUES (%s, %s, %s)',
                    (username, email, password)
                )
            db.commit()
        except IntegrityError as e:
            db.rollback()
            return "Username or email already exists", 400

        return redirect(url_for('login'))

    return render_template('signup.html')

# Fix add_category function
@app.route('/add-category', methods=['GET', 'POST'])
@login_required
def add_category():
    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return "CSRF validation failed", 400

        name = request.form['name'].strip()
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute('INSERT INTO category (name) VALUES (%s)', (name,))
            db.commit()
        except IntegrityError:
            return render_template("add_category.html", error="Category already exists")

        return redirect(url_for('createpost'))

    return render_template("add_category.html")

@app.route('/post/<int:post_id>', methods=['GET'])
def view_post(post_id):
    db = get_db()
    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT post.*, "user".username, category.name as category_name
            FROM post
            JOIN "user" ON post.user_id = "user".id
            LEFT JOIN category ON post.category_id = category.id
            WHERE post.id = %s
        """, (post_id,))
        post = cur.fetchone()
    
    if not post:
        return "Post not found", 404

    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT comment.*, "user".username 
            FROM comment
            JOIN "user" ON comment.user_id = "user".id
            WHERE comment.post_id = %s
            ORDER BY comment.timestamp DESC
        """, (post_id,))
        comments = cur.fetchall()

    return render_template('postdetail.html', post=post, comments=comments)

# Fix add_comment function
@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if not g.user:
        return redirect(url_for('login'))

    text = request.form.get('text')
    if not text:
        return "Comment text is required", 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO comment (post_id, user_id, text, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (post_id, g.user['id'], text, datetime.utcnow()))
    db.commit()

    return redirect(url_for('view_post', post_id=post_id))

# Fix createpost function
@app.route('/createpost', methods=['GET', 'POST'])
@login_required
def createpost():
    db = get_db()

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return "CSRF validation failed", 400

        user_id = session['user_id']
        title = request.form['title']
        content = request.form['content']
        draft = bool(request.form.get('draft'))
        category_id = request.form.get('category_id') or None

        featured_image = None
        if 'featured_image' in request.files:
            image = request.files['featured_image']
            if image and image.filename:
                image_path = os.path.join('static/images', image.filename)
                image.save(image_path)
                featured_image = image.filename

        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO post (title, body, draft, user_id, category_id, featured_image)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, content, draft, user_id, category_id, featured_image))
        db.commit()

        return redirect(url_for('index'))

    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id, name FROM category")
        categories = cur.fetchall()
    return render_template('createpost.html', categories=categories)

# Fix index function
@app.route('/')
def index():
    db = get_db()
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()

    query = """
    SELECT 
        post.id, 
        post.title, 
        post.timestamp, 
        post.featured_image,
        post.category_id, -- ✅ Needed for category links
        "user".username,
        category.name AS category_name,
        (SELECT COUNT(*) FROM comment WHERE comment.post_id = post.id) AS comment_count
    FROM post
    JOIN "user" ON post.user_id = "user".id
    LEFT JOIN category ON post.category_id = category.id
    WHERE post.draft = false
"""

    params = []

    if search:
        query += " AND post.title ILIKE %s"
        params.append(f"%{search}%")

    if category_id:
        query += " AND post.category_id = %s"
        params.append(category_id)

    query += " ORDER BY post.timestamp DESC"

    with db.cursor() as cur:
        cur.execute(query, params)
        posts = cur.fetchall()

        cur.execute("SELECT id, name FROM category ORDER BY name ASC")
        categories = cur.fetchall()

    return render_template(
        'index.html',
        posts=posts,
        categories=categories,
        search=search,
        category_id=category_id
    )

@app.route('/category/<int:category_id>')
def category_view(category_id):
    db = get_db()

    query = """
        SELECT 
            post.id, 
            post.title, 
            post.timestamp, 
            post.featured_image,
            post.category_id,  -- ✅ include this
            "user".username,
            category.name AS category_name,
            (SELECT COUNT(*) FROM comment WHERE comment.post_id = post.id) AS comment_count
        FROM post
        JOIN "user" ON post.user_id = "user".id
        LEFT JOIN category ON post.category_id = category.id
        WHERE post.draft = false
          AND post.category_id = %s
        ORDER BY post.timestamp DESC
    """

    with db.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (category_id,))
        posts = cur.fetchall()

        cur.execute("SELECT id, name FROM category")
        categories = cur.fetchall()

    return render_template(
        'index.html',
        posts=posts,
        categories=categories,
        search='',
        category_id=str(category_id)
    )


# Fix login function
@app.route('/login', methods=['GET', 'POST'])
def login():
    db = get_db()

    if request.method == 'POST':
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return "CSRF validation failed", 400

        username = request.form.get('username')
        password = request.form.get('password')

        with db.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                'SELECT * FROM "user" WHERE username = %s AND password = %s',
                (username, password)
            )
            user = cur.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# if __name__ == '__main__':

#     with app.app_context():
#         init_db()
    
#     app.run(debug=True, host='0.0.0.0', port=5000)