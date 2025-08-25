.PHONY:install
install:
	pip install .

.PHONY: clean
clean:
	rm -rf venv
	find . -iname "*.pyc" -delete

.PHONY: compile
compile:
	python -m compileall .

.PHONY: test
test:
	python -m unittest discover