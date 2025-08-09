CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    bio TEXT DEFAULT '',
    avatar TEXT DEFAULT 'default.png'
);

CREATE TABLE IF NOT EXISTS category (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS post (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    featured_image TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    draft BOOLEAN DEFAULT FALSE,
    reading_time INTEGER,
    views INTEGER DEFAULT 0,
    user_id INTEGER NOT NULL,
    category_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (category_id) REFERENCES category(id)
);

CREATE TABLE IF NOT EXISTS comment (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    parent_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(id),
    FOREIGN KEY (post_id) REFERENCES post(id),
    FOREIGN KEY (parent_id) REFERENCES comment(id)
);
