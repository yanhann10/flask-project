from flask import Flask, render_template, session, redirect, url_for, jsonify
from app import app
import pandas as pd
import os
# FORM
from flask_wtf import FlaskForm
from wtforms import StringField, StringField, SubmitField, validators
from wtforms.widgets import TextArea
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
    input_txt = StringField('Paste text or url(s) below',
                            [validators.required()], widget=TextArea(),
                            render_kw={"style": "width: 100%; height: 100px"})
    output_len = StringField('Enter desired output length in number of words or ratio of the original text',
                             [validators.required()],
                             render_kw={"style": "width: 100%; height: 30px"})
    submit = SubmitField('Summarize', render_kw={"class": "btn btn-light",
                                                 "style": "width: 100px; height: 36px"})


def checkInputFormat(input):
    """check if input is raw text, url or else"""
    if bool(re.match('http', input.replace("\"", "").strip(), re.I)):
        inputFormat = "url"
    elif sum([t.isalpha() for t in list(input)]) > len(input)/2:
        inputFormat = "text"
    else:
        inputFormat = "invalid"
    return inputFormat


def checkOutputFormat(output_len):
    """check if output length is word count or percentage ratio of the original text"""
    if float(output_len) < 1:
        outputFormat = 'ratio'
    else:
        outputFormat = 'word_count'
    return outputFormat


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
    if page.status_code == 200 and getUrlEnding(url) not in ['.pdf', '.ppt']:
        if getUrlEnding(url) == '.txt':
            txt = page.text
        else:
            soup = BeautifulSoup(page.text, 'html.parser')
            p = soup.find_all('p')
            h = max([i.get_text().replace("\n", "").strip()
                     for i in soup.find_all('h1')], key=len)
            txt = ' '.join([i.get_text().replace("\"", "\'")
                            for i in p]).replace('\n', ' ')
    else:
        txt = 'Content of the site not supported'
    return h, txt


def timeSaved(txt, smry_result):
    time_original = len(txt.split(' '))/250
    time_smry = len(smry_result.split(' '))/250
    return round(time_original-time_smry, 1)


# @app.route('/loaderio-3fb2593d333ba9e44c4e66e7a37cb458')
# def load():
#     return "loaderio-3fb2593d333ba9e44c4e66e7a37cb458"


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ReadingForm()
    if form.validate_on_submit():
        session['input_txt'] = form.input_txt.data
        session['output_len'] = form.output_len.data
        return redirect(url_for("summarizeText"))
    return render_template('index.html', form=form)


@app.route('/summarizeText', methods=['GET', 'POST'])
def summarizeText():
    txt = session['input_txt']
    wrd = session['output_len']
    inputFormat = checkInputFormat(txt)
    header = []
    smry = []
    time_saved = []
    article_len = []
    key_words = []
    n = 1

    if inputFormat == 'text':
        gensim_result = summarize(txt, word_count=int(wrd)) if checkOutputFormat(
            wrd) == 'word_count' else summarize(txt, ratio=float(wrd))
        # fallback measure if every sentence in the text is long
        smry_result = gensim_result if len(
            gensim_result) > 0 else '. '.join(txt.split('.', 3)[:3])
        header.append('summary')
        smry.append(smry_result)
        time_saved.append(timeSaved(txt, smry_result))
        kword = keywords(txt, words=3, lemmatize=True,
                         pos_filter=['NN', 'NNS'])
        key_words.append(kword.split('\n'))
        article_len.append(len(txt.split(' ')))
    elif inputFormat == 'url':
        for url in splitUrl(txt.replace("\"", "")):
            h, t = getText(url)
            header.append(h)
            gensim_result = summarize(t, word_count=int(wrd)) if checkOutputFormat(
                wrd) == 'word_count' else summarize(t, ratio=float(wrd))
            smry_result = gensim_result if len(
                gensim_result) > 0 else '. '.join(t.split('.', 3)[:3])
            smry.append(smry_result)
            time_saved.append(timeSaved(t, smry_result))
            kword = keywords(t, words=3, lemmatize=True,
                             pos_filter=['NN', 'NNS'])
            key_words.append(kword.split('\n'))
            article_len.append(len(t.split(' ')))
    n = len(smry)

    return render_template('smry.html', header=header, smry=smry,
                           time_saved=round(sum(time_saved), 2), article_len=article_len,
                           n=n, key_words=key_words)


@app.route('/about')
def about():
    return render_template("about.html")
