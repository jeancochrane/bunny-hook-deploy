from flask import Flask, g

app = Flask('api')

from api import routes
from api.secrets import TOKENS

with app.app_context():
    # Bind secret tokens to the application context
    g.tokens = TOKENS
