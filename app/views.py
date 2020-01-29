from flask import Flask, render_template, session, redirect, url_for, session, jsonify
from app import app
import pandas as pd
import os
# FORM
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
# TEXT
from gensim.summarization.summarizer import summarize
from gensim.summarization import keywords
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "flask-266401-988bfe311e55.json"
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

# define input


class ReadingForm(FlaskForm):
    sep_len = TextField('Enter a list of readings')
    output_len = TextField('Enter desired output in number of words')
    submit = SubmitField('Analyze')


@app.route('/', methods=['GET', 'POST'])
def index():

    # Create instance of the form.
    form = ReadingForm()
    # Check validity of the form
    if form.validate_on_submit():
        session['sep_len'] = form.sep_len.data
        session['output_len'] = form.output_len.data
        return redirect(url_for("summarizeTxt"))
    return render_template('index.html', form=form)


@app.route('/summarizeTxt')
def summarizeTxt():
    txt = session['sep_len']
    wrd = session['output_len']
    smry = summarize(txt, word_count=int(wrd))
    # return smry
    return render_template('smry.html', smry=smry)


@app.route('/about')
def about():
    return render_template("about.html")
