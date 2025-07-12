from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', 
                             validators=[DataRequired(), EqualTo('password')])

class QuestionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=10, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20)])
    tags = StringField('Tags (comma-separated)', validators=[DataRequired()])

class AnswerForm(FlaskForm):
    content = TextAreaField('Your Answer', validators=[DataRequired(), Length(min=20)])

class SearchForm(FlaskForm):
    query = StringField('Search questions...', validators=[DataRequired()])
