from flask import Flask
from flask_oidc import OpenIDConnect

oidc = OpenIDConnect()
app = Flask(__name__)

app.config.update({
    'OIDC_CLIENT_SECRETS': 'client_secrets.json',
    'OIDC_OPENID_REALM': 'master',
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post',
    'OIDC_TOKEN_TYPE_HINT': 'access_token',
    'OIDC-SCOPES': ['openid']
})

oidc.init_app(app)
