# init_db.py
from app import app, db

# push an application context, then create all tables
with app.app_context():
    db.create_all()
    print("✅ Database initialized (site.db created).")
