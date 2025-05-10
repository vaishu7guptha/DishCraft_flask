from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    posts    = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    title   = db.Column(db.String(100), nullable=False)
    body    = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Recipe(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(120), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    cuisine    = db.Column(db.String(30), nullable=False)
    dietary    = db.Column(db.String(30), nullable=False)
    count      = db.Column(db.Integer, nullable=False)
    image_url  = db.Column(db.String(500), nullable=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id    = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments   = db.relationship('Comment', backref='recipe', lazy=True)
    user = db.relationship('User', backref='recipes', lazy=True)

# models.py

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='comments')  # ← this line enables c.user
