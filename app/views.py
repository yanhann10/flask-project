from flask import Flask, render_template, session, redirect, url_for, session, jsonify
from app import app
import pandas as pd
import os
# FORM
from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
# SCRAP
import requests
from bs4 import BeautifulSoup
# TEXT
import re
from gensim.summarization.summarizer import summarize
from gensim.summarization import keywords

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "flask-266401-988bfe311e55.json"
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


class ReadingForm(FlaskForm):
    """input form"""
    sep_len = TextField('Paste the text of the reading here')
    input_url = TextField('Or enter a list of url instead')
    output_len = TextField('Enter desired output in number of words')

    submit = SubmitField('Synthesize')


def checkInputFormat(input):
    """check if input is raw text, url or else"""
    if len(re.findall("http", input)) > 1:
        inputFormat = "urllst"
    elif bool(re.match('http', input, re.I)):
        inputFormat = "url"
    elif sum([t.isalpha() for t in list(input)]) > len(input)/2:
        inputFormat = "text"
    else:
        inputFormat = "invalid"
    return inputFormat


def getText(url):
    """parse text on the web page"""
    page = requests.get(url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.text, 'html.parser')
        #h = soup.find_all('h1')[0]
        p = soup.find_all('p')
        txt = ''.join([i.get_text() for i in p]).replace('\n', '')
    else:
        txt = 'Content of the site not supported'
    return txt


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ReadingForm()

    if form.validate_on_submit():
        session['sep_len'] = form.sep_len.data
        session['input_url'] = form.input_url.data
        session['output_len'] = form.output_len.data
        return redirect(url_for("summarizeTxt"))
    return render_template('index.html', form=form)


@app.route('/summarizeTxt', methods=['GET', 'POST'])
def summarizeTxt():
    txt = session['sep_len']
    url = session['input_url']
    wrd = session['output_len']
    if txt is not None:
        smry = summarize(txt, word_count=int(wrd))
    elif url is not None:
        txt = getText(url)
        smry = summarize(txt, word_count=int(wrd))
    return render_template('smry.html', head='Article summary', smry=smry)


@app.route('/about')
def about():
    return render_template("about.html")
