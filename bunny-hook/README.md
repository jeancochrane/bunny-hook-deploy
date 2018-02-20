# Bunny Hook
🐇↩️ A simple but flexible webhook for deploying any kind of app directly from GitHub.

Currently under rapid development.

## Requirements

Install Python requirements:

```bash
pip install -U -r requirements.txt
```

## Running tests

```bash
python -m unittest discover -s tests
```

## Running the hook

In one shell:

```bash
# Run the API server
python runserver.py
```

In another shell:

```bash
# Run the build queue
python runqueue.py
```
