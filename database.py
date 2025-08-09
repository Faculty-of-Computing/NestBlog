import psycopg2
from psycopg2.extras import RealDictCursor
from flask import g, current_app

def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(
            dbname=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            host=current_app.config['DB_HOST'],
            port=current_app.config.get('DB_PORT', 5432),
            cursor_factory=RealDictCursor
        )
    return g.db

def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with current_app.app_context():
        db = get_db()
        with db.cursor() as cursor:
            with open('schema.sql', 'r') as f:
                cursor.execute(f.read())
            db.commit()
        print("Initialized the PostgreSQL database.")
