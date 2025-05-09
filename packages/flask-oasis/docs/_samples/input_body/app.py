from dataclasses import dataclass, field

import zangar as z
from flask import Flask
from flask_oasis import MediaType, PathTemplate, Resource, input, output, responseify


@dataclass
class LoginForm:
    username: str
    password: str = field(
        metadata={"zangar": {"schema": z.str(meta={"oas": {"format": "password"}})}}
    )


class Login(Resource):
    @input.body(
        "form",
        content={
            "application/x-www-form-urlencoded": MediaType(z.dataclass(LoginForm)),
            "application/json": MediaType(z.dataclass(LoginForm)),
        },
        description='Support "application/x-www-form-urlencoded" and "application/json" content types',
    )
    @output.response(200, content={"text/plain": MediaType()})
    def post(self, form: LoginForm):
        return responseify("Welcome, %s!" % form.username)


paths = {
    PathTemplate("/login"): Login,
}

app = Flask(__name__)
for path, resource in paths.items():
    app.add_url_rule(path.flask_path, view_func=resource.as_view())
