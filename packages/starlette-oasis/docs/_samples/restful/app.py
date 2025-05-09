from __future__ import annotations

from dataclasses import asdict, dataclass, field

import zangar as z
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from starlette_oasis import (
    MediaType,
    PathTemplate,
    Resource,
    input,
    output,
    responseify,
)


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
    async def get(self, request, paging: Paging):
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
    async def post(self, request, data: dict):
        user = User(id=USERS[-1].id + 1, **data)
        USERS.append(user)
        return responseify(user)


class UserAPI(Resource):
    @input.path("uid", z.to.int(), description="User ID")
    @output.response(404)
    async def dispatch(self, request, uid):
        for user in USERS:
            if user.id == uid:
                self.user = user
                break
        else:
            return Response(status_code=404)
        return await super().dispatch(request, uid)

    @output.response(
        200,
        content={
            "application/json": MediaType(z.dataclass(User).transform(asdict)),
        },
    )
    async def get(self, request, uid):
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
    async def patch(self, request, uid, data: dict):
        for k, v in data.items():
            setattr(self.user, k, v)
        return responseify(self.user)

    @output.response(204)
    async def delete(self, request, uid):
        USERS.remove(self.user)
        return Response(status_code=204)


paths: dict[PathTemplate, type[Resource]] = {
    PathTemplate("/users"): UsersAPI,
    PathTemplate("/users/{uid}"): UserAPI,
}


app = Starlette(
    routes=[Route(path.starlette_path, resource) for path, resource in paths.items()],
)
