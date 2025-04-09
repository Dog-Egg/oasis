from dataclasses import asdict, dataclass

import zangar as z
from flask import abort
from flask_oasis import MediaType, Resource, input, output, responseify


@dataclass
class User:
    id: int
    name: str
    age: int


USERS = [
    User(1, "James", 20),
    User(2, "Linda", 42),
    User(3, "Emily", 18),
]


class Users(Resource):
    @input.path("uid", z.to.int())
    @output.response(
        200,
        content={
            "application/json": MediaType(
                z.dataclass(User).transform(asdict),
            )
        },
    )
    @output.response(404)
    def get(self, uid):
        for user in USERS:
            if user.id == uid:
                return responseify(user)
        else:
            abort(404)
