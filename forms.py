from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(2,20)])
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm  = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit   = SubmitField('Sign Up')
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('Username taken.')
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('Email already registered.')

class LoginForm(FlaskForm):
    email    = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Log In')

class PostForm(FlaskForm):
    title  = StringField('Title', validators=[DataRequired(), Length(max=100)])
    body   = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('Post')

class RecipeForm(FlaskForm):
    ingredients = StringField('Ingredients', validators=[DataRequired()])
    cuisine     = SelectField('Cuisine', choices=[('any','Any'),('italian','Italian'),('indian','Indian'),('mexican','Mexican')])
    dietary     = SelectField('Dietary', choices=[('none','None'),('vegetarian','Vegetarian'),('vegan','Vegan'),('gluten-free','Gluten‑Free')])
    count       = IntegerField('How many recipes?', default=1, validators=[DataRequired()])
    submit      = SubmitField('Generate')

class CommentForm(FlaskForm):
    body   = TextAreaField('Comment', validators=[DataRequired()], render_kw={"rows":3})
    rating = SelectField('Rating', 
                choices=[(str(i), '★'*i) for i in range(1,6)],
                validators=[DataRequired()])
    submit = SubmitField('Post')
