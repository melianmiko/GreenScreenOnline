import json
import logging

import flask
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from green_screen_online import queue_handler, auto_cleanup
from green_screen_online.queue_managment import PendingTask

MAX_VIDEO_FILE_SIZE = 50 * 1024 * 1024

log = logging.getLogger("FlaskApp")
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
limiter = Limiter(get_remote_address, app=app)

logging.basicConfig(level=logging.DEBUG)
queue_handler.start()
auto_cleanup.start()


@app.after_request
def after_rq(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT'
    return response


@app.route("/robots.txt")
def robots():
    return flask.send_file("static/robots.txt")


@app.route("/")
def index_page():
    """
    Возвращает основной HTML-файл
    """
    return flask.send_file("index.html")


@app.route("/api/requests", methods=["PUT"])
# @limiter.limit("1/minute")
def put_request():
    """
    Принимает новое задание
    :return:
    """
    try:
        config = request.form["config"]
        assert len(config) < 4096
        config = json.loads(config)

        base_video = request.files["base_video"]
        assert base_video.stream.tell() < MAX_VIDEO_FILE_SIZE
        assert base_video.mimetype.startswith("video/")
        overlay_video = request.files["overlay_video"]
        assert overlay_video.stream.tell() < MAX_VIDEO_FILE_SIZE
        assert overlay_video.mimetype.startswith("video/")

        entry = PendingTask.register(config)

        base_video.save(entry.temp_dir / "base_video")
        overlay_video.save(entry.temp_dir / "overlay_video")
        return {"id": entry.ident}, 202
    except (AssertionError, json.JSONDecodeError):
        return {"error": "Invalid request"}, 400


@app.route("/api/requests/<task_id>")
@limiter.limit("1/second")
def get_task_status(task_id):
    """
    Возвращает статус задачи
    """
    return {
        "status": PendingTask.get_status(task_id)
    }


@app.route("/api/requests/<task_id>/<path:filename>")
def get_task_artifact(task_id, filename):
    """
    Отдаёт файл от задачи (используется для получения итогового видео)
    """
    try:
        entry = PendingTask.all_tasks[task_id]
        return flask.send_from_directory(entry.temp_dir, filename)
    except KeyError:
        return {"error": "task not found"}, 404


if __name__ == '__main__':
    app.run()
