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
    sep_len = TextField('Paste below text or url(s)',
                        render_kw={"style": "width: 100%; height: 100px"})
    output_len = TextField('Enter desired output in number of words',
                           render_kw={"style": "width: 100%; height: 30px"})
    submit = SubmitField('Summarize', render_kw={"class": "btn btn-light"})


def checkInputFormat(input):
    """check if input is raw text, url or else"""
    if bool(re.match('http', input.replace("\"", "").strip(), re.I)):
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


def getUrlEnding(url):
    return url.rsplit('/', 1)[-1][-4:]


def getText(url):
    """parse text on the web page"""
    page = requests.get(url)
    h = ""
    if page.status_code == 200 and getUrlEnding(url) not in ['.txt', '.pdf', '.ppt']:
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


def timeSaved(txt, smry_result):
    time_original = len(txt.split(' '))/250
    time_smry = len(smry_result.split(' '))/250
    return round(time_original-time_smry, 1)


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
    key_words = []
    n = 1

    if inputFormat == 'text':
        smry_result = summarize(txt, word_count=int(wrd))
        header.append('summary')
        smry.append(smry_result)
        time_saved.append(timeSaved(txt, smry_result))
        kword = keywords(txt, words=3, lemmatize=True,
                         pos_filter=['NN', 'NNS'])
        key_words.append(kword.split('\n'))
    elif inputFormat == 'url':
        for url in splitUrl(txt.replace("\"", "")):
            h, t = getText(url)
            header.append(h)
            smry_result = summarize(t, word_count=int(wrd)) if len(
                summarize(t, word_count=int(wrd))) > 0 else t[:100]
            smry.append(smry_result)
            time_saved.append(timeSaved(t, smry_result))
            kword = keywords(t, words=3, lemmatize=True,
                             pos_filter=['NN', 'NNS'])
            key_words.append(kword.split('\n'))
    n = len(smry)

    return render_template('smry.html', header=header, smry=smry, time_saved=sum(time_saved), n=n, key_words=key_words)


@app.route('/about')
def about():
    return render_template("about.html")
