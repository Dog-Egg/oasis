from flask import jsonify, make_response, request


def json_response_processor(kwargs):
    return make_response(jsonify(kwargs["data"]), kwargs["status"])


def json_request_processor():
    return request.json


def form_request_processor():
    return request.form


def text_response_processor(kwargs):
    response = make_response(kwargs["data"], kwargs["status"])
    response.mimetype = "text/plain"
    return response
