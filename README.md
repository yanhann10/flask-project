# A Flask Web App for summarize readings

_Quick, read_ is an app for summarize readings and potentially generate writeups (under development)

Accepted formats include text and webpages

## Demo

To be added

## Set up

To run it locally, git clone this repo, set up virtual environment

```
virtualenv --python python3 venv
source venv/bin/activate
```

And complete the following steps

Install dependencies

```
make install
```

Running the app locally

```
export FLASK_APP=run.py
flask run
```

## Tools

Flask, Flask-WTF, BeautifulSoup, Gensim and Google CloudBuild for continuous deployment

## License

MIT
