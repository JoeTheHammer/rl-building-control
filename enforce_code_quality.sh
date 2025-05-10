# enforce_code_quality.sh
#!/bin/bash
pipenv run isort .
pipenv run black .
pipenv run flake8 .
