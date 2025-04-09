from dataclasses import asdict, dataclass, field

import zangar as z
from django.http import Http404, HttpResponse
from django_oasis import MediaType, Resource, input, output, responseify


@dataclass
class User:
    id: int
    name: str


USERS = [
    User(1, "James"),
    User(2, "Linda"),
    User(3, "Emily"),
]


@dataclass
class Paging:
    page: int = field(default=1, metadata={"zangar": {"schema": z.to.int()}})
    page_size: int = field(default=10, metadata={"zangar": {"schema": z.to.int()}})


class UsersAPI(Resource):
    @input.query("paging", z.dataclass(Paging), required=False)
    @output.response(
        200,
        content={
            "application/json": MediaType(
                z.struct(
                    {
                        "users": z.list(z.dataclass(User).transform(asdict)),
                        "page": z.int(),
                        "page_size": z.int(),
                    }
                )
            )
        },
    )
    def get(self, request, paging: Paging):
        offset = (paging.page - 1) * paging.page_size
        return responseify(
            {
                "users": USERS[offset : offset + paging.page_size],
                "page": paging.page,
                "page_size": paging.page_size,
            }
        )

    @input.body(
        "data",
        content={
            "application/json": MediaType(z.dataclass(User).struct.omit_fields(["id"])),
        },
    )
    @output.response(
        201,
        content={
            "application/json": MediaType(z.dataclass(User).transform(asdict)),
        },
    )
    def post(self, request, data: dict):
        user = User(id=USERS[-1].id + 1, **data)
        USERS.append(user)
        return responseify(user)


class UserAPI(Resource):
    @input.path("uid", z.to.int(), description="User ID")
    @output.response(404)
    def dispatch(self, request, uid):
        for user in USERS:
            if user.id == uid:
                self.user = user
                break
        else:
            raise Http404
        return super().dispatch(request, uid)

    @output.response(
        200,
        content={
            "application/json": MediaType(z.dataclass(User).transform(asdict)),
        },
    )
    def get(self, request, uid):
        return responseify(self.user)

    @input.body(
        "data",
        content={
            "application/json": MediaType(
                z.dataclass(User).struct.omit_fields(["id"]).optional_fields()
            ),
        },
    )
    @output.response(
        200,
        content={
            "application/json": MediaType(z.dataclass(User).transform(asdict)),
        },
    )
    def patch(self, request, uid, data: dict):
        for k, v in data.items():
            setattr(self.user, k, v)
        return responseify(self.user)

    @output.response(204)
    def delete(self, request, uid):
        USERS.remove(self.user)
        return HttpResponse(status=204)
