#
# App server
#
# Nothing here as it's just to serve /static.
#
from flask import Flask

app = Flask(__name__)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005)
