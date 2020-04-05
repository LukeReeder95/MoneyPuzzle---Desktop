import base64
import json
import os
import webbrowser
import io

from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    url_for,
    render_template,
    jsonify,
    request,
    make_response,
    send_file,
)
import webview

server = Flask(__name__)
server.config["SEND_FILE_MAX_AGE_DEFAULT"] = 1  # disable caching


def verify_token(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        data = json.loads(request.data)
        token = data.get("token")
        if token == webview.token:
            return function(*args, **kwargs)
        else:
            raise Exception("Authentication error")

    return wrapper


@server.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@server.route("/")
def landing():
    """
    Render initial html template for the application
    """
    return render_template("index.html", token=webview.token)


@server.route("/savefile", methods=["POST"])
def savefile():
    """
    Open save file selection
    return
    """
    body = request.get_json()
    filetype = body["filetype"]
    print(filetype)
    print(body["data"])
    destination_path = webview.windows[0].create_file_dialog(
        webview.SAVE_DIALOG,
        directory="",
        save_filename="filename",
        # file_types=("Text, JSON, png jpg(*.txt;*.JSON;*.png;*.jpg) ",),
    )
    try:
        destination_path = Path(destination_path)
    except TypeError:
        return jsonify(saved=False, message="Save dialog cancelled")

    if filetype in ["json", "txt"]:
        with open(destination_path, "w+") as destination_file:
            destination_file.write(body["data"])
    # elif filetype == "txt":
    #     with open(destination_path, "w+") as destination_file:
    #         destination_file.write(body["data"])
    elif filetype in ["png", "jpg"]:
        with open(destination_path, "wb+") as destination_file:
            data = body["data"].split(",", 1)[1]
            destination_file.write(base64.b64decode(data))

    else:
        raise TypeError(f"Unknown filetype provided, {filetype}")

    return jsonify(saved=True)


@server.route("/fullscreen", methods=["POST"])
@verify_token
def fullscreen():
    webview.windows[0].toggle_fullscreen()
    return jsonify({})


@server.route("/open-url", methods=["POST"])
@verify_token
def open_url():
    url = request.json["url"]
    webbrowser.open_new_tab(url)

    return jsonify({})


def run_server():
    server.run(host="127.0.0.1", port=23948, threaded=True)


if __name__ == "__main__":
    run_server()
