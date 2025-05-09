import os
import typing

import nox


def install_package(session: nox.Session):
    pyproject = nox.project.load_toml()
    dependencies = pyproject["project"]["dependencies"]
    session.install(*dependencies)
    session.install("--force-reinstall", "--no-deps", ".")


@nox.session(python=["3.8"])
def test_django_oasis(session: nox.Session):
    with session.chdir("packages/django-oasis"):
        install_package(session)
        session.install("pytest", "beautifulsoup4", "PyYAML")
        session.run("pytest")


@nox.session(python=["3.8"])
def test_flask_oasis(session: nox.Session):
    with session.chdir("packages/flask-oasis"):
        install_package(session)
        session.install("pytest", "PyYAML")
        session.run("pytest")


@nox.session(python=["3.8"])
def test_starlette_oasis(session: nox.Session):
    with session.chdir("packages/starlette-oasis"):
        install_package(session)
        session.install("pytest", "httpx", "pytest-asyncio")
        session.run("pytest")


@nox.session
@nox.parametrize("command", ["dev", "build"])
@nox.parametrize("package", os.listdir("packages"))
def doc(
    session: nox.Session,
    package: str,
    command: typing.Literal["dev", "build"],
):
    session.install(
        "snowballstemmer==2.2.0"
    )  # 这是 Sphinx 的依赖包，目前最新版本有问题，所以这里手动安装旧版本。
    session.install("-e", f"packages/{package}")
    session.install("jsonschema")

    if command == "dev":
        session.install("sphinx-autobuild")
        session.run(
            "sphinx-autobuild",
            *session.posargs,
            f"packages/{package}/docs",
            f"docs/_build/{package}",
        )

    if command == "build":
        session.install("sphinx")
        session.run(
            "sphinx-build",
            *session.posargs,
            f"packages/{package}/docs",
            f"docs/_build/{package}",
        )


@nox.session
def lint(session: nox.Session):
    session.install("pre-commit")
    session.run(
        "pre-commit",
        "run",
        "--all-files",
        "--show-diff-on-failure",
    )


nox.options.reuse_venv = "yes"
nox.options.sessions = [
    "test_django_oasis",
    "test_flask_oasis",
    "test_starlette_oasis",
    "lint",
    "doc(package='flask-oasis', command='build')",
    "doc(package='starlette-oasis', command='build')",
    "doc(package='django-oasis', command='build')",
]
