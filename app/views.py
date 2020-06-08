from flask import Flask, render_template, session, redirect, url_for, jsonify
from app import app
import pandas as pd
import os

# FORM
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField, validators
from wtforms.widgets import TextArea

# SCRAP
import requests
from bs4 import BeautifulSoup

# TEXT
import re
from gensim.summarization.summarizer import summarize
from gensim.summarization import keywords
from transformers import pipeline

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "flask-266401-988bfe311e55.json"
SECRET_KEY = os.urandom(32)
app.config["SECRET_KEY"] = SECRET_KEY
# abstract_summarizer = pipeline(
#             "summarization", model="t5-base", tokenizer="t5-base"
#         )


# TODO:
# [ ] Fix RadioField issue
# [ ] Token indices sequence length
# [ ] Validate output length is shorter than input length


class ReadingForm(FlaskForm):
    """input form"""

    input_txt = StringField(
        "Paste text or url(s) below",
        [validators.required()],
        widget=TextArea(),
        render_kw={"style": "width: 100%; height: 100px"},
    )
    output_len = StringField(
        "Enter desired output length in number of words or ratio of the original text",
        [validators.required()],
        render_kw={"style": "width: 100%; height: 30px"},
    )
    # smry_type = StringField(
    #     "Select summary type: 1 for extractive or 2 for abstractive (under development)",
    #     [validators.required()],
    #     render_kw={"style": "width: 100%; height: 30px"},
    # )

    # smry_type = RadioField(
    #     "Select summary methods",
    #     choices=["Extractive summary", "Abstractive summary"],
    #     default="Extractive summary",
    # )
    submit = SubmitField(
        "Summarize",
        render_kw={"class": "btn btn-light", "style": "width: 100px; height: 36px"},
    )


def checkInputFormat(input):
    """check if input is raw text, url or else"""
    if bool(re.match("http", input.replace('"', "").strip(), re.I)):
        inputFormat = "url"
    elif sum([t.isalpha() for t in list(input)]) > len(input) / 2:
        inputFormat = "text"
    else:
        inputFormat = "invalid"
    return inputFormat


def checkOutputFormat(output_len):
    """check if output length is word count or percentage ratio of the original text"""
    if float(output_len) < 1:
        outputFormat = "ratio"
    else:
        outputFormat = "word_count"
    return outputFormat


def calcOutputLen(outputFormat, article_len, wrd):
    """calc length of the summary. wrd is the user-specified output length or ratio"""
    if outputFormat == "word_count":
        return int(wrd)
    else:
        return article_len * float(wrd)


def generate_smry(smry_type, text, word_count):
    """generate summary: extractive (original words) or abstractive (synthesized) """
    if smry_type == "1":
        # use gensim
        return summarize(text, word_count=word_count)
    else:
        # use transformer T5

        # return abstract_summarizer(text, min_length=5, max_length=word_count)[0][
        #     "summary_text"
        # ]
        pass


def splitUrl(urllst):
    """when there are multiple urls, split them into individual ones to parse"""
    urls = [
        "http" + i.replace("\n", "").replace('"', "").strip()
        for i in urllst.split("http")
    ]
    if "http" in urls:
        urls.remove("http")
    return urls


def getUrlEnding(url):
    return url.rsplit("/", 1)[-1][-4:]


def getText(url):
    """parse text on the web page"""
    page = requests.get(url)
    h = ""
    if page.status_code == 200 and getUrlEnding(url) not in [".pdf", ".ppt"]:
        if getUrlEnding(url) == ".txt":
            txt = page.text
        else:
            soup = BeautifulSoup(page.text, "html.parser")
            p = soup.find_all("p")
            h = max(
                [i.get_text().replace("\n", "").strip() for i in soup.find_all("h1")],
                key=len,
            )
            txt = " ".join([i.get_text().replace('"', "'") for i in p]).replace(
                "\n", " "
            )
    else:
        txt = "Content of the site not supported"
    return h, txt


def timeSaved(txt, smry_result):
    time_original = len(txt.split(" ")) / 250
    time_smry = len(smry_result.split(" ")) / 250
    return round(time_original - time_smry, 1)


@app.route("/", methods=["GET", "POST"])
def index():
    form = ReadingForm()
    if form.validate_on_submit():
        session["input_txt"] = form.input_txt.data
        session["output_len"] = form.output_len.data
        # session["smry_type"] = form.smry_type.data
        return redirect(url_for("summarizeText"))
    return render_template("index.html", form=form)


@app.route("/summarizeText", methods=["GET", "POST"])
def summarizeText():
    txt = session["input_txt"]
    wrd = session["output_len"]
    # smry_type = session["smry_type"]
    smry_type = "1"  # temp
    inputFormat = checkInputFormat(txt)
    header = []
    smry = []
    time_saved = []
    article_len = []
    key_words = []
    n = 1

    if inputFormat == "text":
        l = len(txt.split(" "))
        article_len.append(l)
        wrd_cnt = calcOutputLen(checkOutputFormat(wrd), l, wrd)
        gensim_result = generate_smry(smry_type, txt, wrd_cnt)
        # fallback measure if every sentence in the text is long
        smry_result = (
            gensim_result
            if len(gensim_result) > 0
            else ". ".join(txt.split(".", 3)[:3])
        )
        header.append("summary")
        smry.append(smry_result)
        time_saved.append(timeSaved(txt, smry_result))
        kword = keywords(txt, words=3, lemmatize=True, pos_filter=["NN", "NNS"])
        key_words.append(kword.split("\n"))

    elif inputFormat == "url":
        for url in splitUrl(txt.replace('"', "")):
            h, t = getText(url)
            l = len(t.split(" "))
            article_len.append(l)
            header.append(h)
            # default to 20% in case the entered word count is higher than the original word count
            wrd_cnt = calcOutputLen(checkOutputFormat(wrd), l, wrd)
            gensim_result = generate_smry(smry_type, t, wrd_cnt)
            smry_result = (
                gensim_result
                if len(gensim_result) > 0
                else ". ".join(t.split(".", 3)[:3])
            )
            smry.append(smry_result)
            time_saved.append(timeSaved(t, smry_result))
            kword = keywords(t, words=3, lemmatize=True, pos_filter=["NN", "NNS"])
            key_words.append(kword.split("\n"))

    n = len(smry)

    return render_template(
        "smry.html",
        header=header,
        smry=smry,
        time_saved=round(sum(time_saved), 2),
        article_len=article_len,
        n=n,
        key_words=key_words,
    )


@app.route("/about")
def about():
    return render_template("about.html")
