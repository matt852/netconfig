#!/usr/bin/python3

from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """User login form."""

    user = StringField('Username', validators=[DataRequired()], render_kw={'autofocus': True})
    pw = PasswordField('Password', validators=[DataRequired()])
    submit_button = SubmitField('Login')
