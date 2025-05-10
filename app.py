from dotenv import load_dotenv
load_dotenv()

import os
import re
import requests
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from together import Together

# models and forms
from models import db, User, Post, Recipe, Comment
from forms import CommentForm, RecipeForm, RegistrationForm, LoginForm, PostForm

# ─── App & Extensions ───────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET") or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── OpenRouter API Client ──────────────────────────────────
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# ─── Together API Client ────────────────────────────────────
together = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# ─── Login Loader ───────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── AI Recipe Generation ───────────────────────────────────

def generate_recipe(ings, cuisine, dietary, count):
    prompt = (
        f"Generate {count} recipes using only these ingredients:\n{ings}\n\n"
        "Each recipe should follow this exact format:\n\n"
        "Recipe <n>:\n"
        "Title: <Short title>\n"
        "Cuisine: <Cuisine style>\n"
        "Dietary: <Dietary preference>\n"
        "Servings: <Number of servings>\n"
        "Ingredients:\n"
        "- ingredient 1\n"
        "- ingredient 2\n"
        "- ...\n"
        "Steps: Provide at least 6 clear, numbered steps, including cook times, temperatures, and plating tips. For example:\n"
        "1. Preheat the oven to 375°F (190°C). \n"
        "2. Meanwhile, …\n"
        "…\n\n"
        "Make sure each recipe starts with 'Recipe 1:', 'Recipe 2:', etc."
    )


    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",  # Or your live domain
        "X-Title": "Dish Craft"
    }

    body = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 600
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)

    if response.status_code != 200:
        raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ─── Routes ─────────────────────────────────────────────────
@app.route("/")
def intro():
    return render_template("intro.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('recipe'))
        flash("Login failed.", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('intro'))

@app.route("/recipe", methods=["GET", "POST"])
@login_required
def recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        try:
            raw = generate_recipe(
                form.ingredients.data,
                form.cuisine.data,
                form.dietary.data,
                form.count.data
            )
        except Exception:
            flash("Sorry, I couldn’t generate a recipe right now. Please try again.", "danger")
            return render_template("index.html", form=form)

        blocks = re.split(r"(Recipe\s*\d+\s*:)", raw)
        if len(blocks) < 3:
            flash("Sorry, I got an unexpected response format from the AI.", "danger")
            return render_template("index.html", form=form)

        recipes = []
        for i in range(1, len(blocks), 2):
            header = blocks[i].strip()
            body = blocks[i + 1].strip()

            lines = body.splitlines()
            meta_lines = lines[:4]
            content_lines = lines[4:]

            meta = {}
            for m in meta_lines:
                if ":" in m:
                    key, val = m.split(":", 1)
                    meta[key.strip().lower()] = val.strip()

            title = meta.get("title", header)
            cuisine = meta.get("cuisine", form.cuisine.data).lower()
            dietary = meta.get("dietary", form.dietary.data).lower()
            servings = int(meta.get("servings", form.count.data))
            content = "\n".join(content_lines).strip()

            r = Recipe(
                title=title,
                content=content,
                cuisine=cuisine,
                dietary=dietary,
                count=servings,
                image_url=None,
                user_id=current_user.id
            )

            try:
                img_resp = together.images.generate(
                    prompt=f"{r.title}, professional food photography",
                    model="black-forest-labs/FLUX.1.1-pro",
                    steps=20,
                    n=1
                )
                b64 = img_resp.data[0].b64_json
                r.image_url = f"data:image/png;base64,{b64}"
            except Exception as e:
                app.logger.warning("Image generation failed: %s", e)
                r.image_url = None

            db.session.add(r)
            recipes.append(r)

        db.session.commit()
        session['last_recipe_ids'] = [r.id for r in recipes]
        return redirect(url_for('recipes'))

    return render_template("index.html", form=form)

@app.route("/forum", methods=["GET", "POST"])
@login_required
def forum():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('forum'))
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("forum.html", form=form, posts=posts)

@app.route("/recipes", methods=["GET", "POST"])
@login_required
def recipes():
    comment_form = CommentForm()
    ids = session.get('last_recipe_ids', [])
    recipes = Recipe.query.filter(Recipe.id.in_(ids)).order_by(Recipe.id).all() if ids else []

    if comment_form.validate_on_submit():
        cid = request.form.get("recipe_id")
        c = Comment(
            body=comment_form.body.data,
            rating=int(comment_form.rating.data),
            user_id=current_user.id,
            recipe_id=int(cid)
        )
        db.session.add(c)
        db.session.commit()
        session['last_recipe_ids'] = ids
        flash("Comment posted!", "success")
        return redirect(url_for('recipes'))

    return render_template("recipes.html", recipes=recipes, comment_form=comment_form)

# ─── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
