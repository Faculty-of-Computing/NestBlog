# NestBlog

![School Project](https://img.shields.io/badge/School%20Project-✔️-blue)

🎓 **School Project** – Blogging Service built with **Flask (Python)** and **Postgres**, featuring a **frontend built with HTML, CSS, and JavaScript** served via Flask templates.  
📖 **Course:** UUY-CSC222
🏫 **Department:** Computer Science
👥 **Group:** 2
🎓 **Series:** 022/023

Web-based blogging platform built on a monolithic architecture that allows users to create, edit and publish blog posts.
---

## 🚀 Features

- Flask backend with Postgres database
- Frontend served from Flask templates with static assets
- API endpoints for post & category creation, deletion and editing

---

## 🛠️ Tech Stack

- Python 3.x, Flask
- Postgres database
- HTML, CSS, JavaScript served via Flask `templates` and `static` folders

---

## 🔧 Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/Faculty-of-Computing/uuycsc22blogproject.git
cd uuycsc22blogproject
```

### 2. Create and activate a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

To set it up and run on local, get a free PostgreSQL server online. From Supabase for example, or you can just setup PostgreSQL on your PC at once 

```
DB_NAME=databasename
DB_USER=yourusername
DB_PASSWORD=12345678
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your_secret_key
```

### 4. Run the Flask application

```bash
python app.py
```

The app will be available at:

```text
http://localhost:5000
```

---
