from http import HTTPStatus

from flask import jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        payload = {
            "code": error.code,
            "message": error.description,
        }
        return jsonify(payload), error.code

    @app.errorhandler(Exception)
    def handle_uncaught_exception(error):
        app.logger.exception("Unhandled exception: %s", error)
        payload = {
            "code": HTTPStatus.INTERNAL_SERVER_ERROR,
            "message": "Internal server error",
        }
        return jsonify(payload), HTTPStatus.INTERNAL_SERVER_ERROR
