#!/usr/bin/env python3
from webdaemon import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000, use_reloader=True)
