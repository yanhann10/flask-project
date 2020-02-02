from app import app
from flask_cache import Cache
cache = Cache()


def main():
    cache.init_app(app)
    with app.app_context():
        cache.clear()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
