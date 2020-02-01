install:
	pip3 install --upgrade pip && pip3 install -r requirements.txt

test:
	python -m pytest tests/*.py


lint:
	pylint --disable=R,C run.py

all: install lint test