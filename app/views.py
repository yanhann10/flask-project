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
    sep_len = TextField('Paste below text or url(s)')
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


def splitUrl(urllst):
    """when there are multiple urls, split them into individual ones to parse"""
    urls = ['http'+i.replace("\n", "").replace("\"", "").strip()
            for i in urllst.split('http')]
    if 'http' in urls:
        urls.remove('http')
    return urls


def getText(url):
    """parse text on the web page"""
    h = ""
    page = requests.get(url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.text, 'html.parser')
        p = soup.find_all('p')
        h = max([i.get_text().replace("\n", "").strip()
                 for i in soup.find_all('h1')], key=len)
        txt = ''.join([i.get_text().replace("\"", "\'")
                       for i in p]).replace('\n', ' ')
        time_txt = len(txt.split(' '))/250
    else:
        txt = 'Content of the site not supported'
    return h, txt


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ReadingForm()

    if form.validate_on_submit():
        session['sep_len'] = form.sep_len.data
        session['output_len'] = form.output_len.data
        return redirect(url_for("summarizeTxt"))
    return render_template('index.html', form=form)


@app.route('/summarizeTxt', methods=['GET', 'POST'])
def summarizeTxt():
    txt = session['sep_len']
    wrd = session['output_len']
    inputFormat = checkInputFormat(txt)
    header = []
    smry = []
    time_saved = []
    n = 1
    if inputFormat == 'text':
        smry = summarize(txt, word_count=int(wrd))
        time_txt = len(txt.split(' '))/250
    elif inputFormat == 'url':
        header, t = getText(url)
        smry = summarize(t, word_count=int(wrd))
        time_txt = len(t.split(' '))/250
    elif inputFormat == 'urllst':
        for url in splitUrl(txt):
            h, t = getText(url)
            header.append(h)
            smry_url = summarize(t, word_count=int(wrd)) if len(
                summarize(t, word_count=int(wrd))) > 0 else t[:100]
            smry.append(smry_url)
            time_original = len(t.split(' '))/250
            time_smry = len(smry_url.split(' '))/250
            time_saved.append(round(time_original-time_smry, 1))
        n = len(smry)

    return render_template('smry.html', header=header, smry=smry, time_saved=sum(time_saved), n=n)


@app.route('/about')
def about():
    return render_template("about.html")
