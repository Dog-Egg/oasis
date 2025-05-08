import argparse
import os

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
        session.install("pytest")
        session.run("pytest")


@nox.session(python=["3.8"])
def test_starlette_oasis(session: nox.Session):
    with session.chdir("packages/starlette-oasis"):
        install_package(session)
        session.install("pytest", "httpx")
        session.run("pytest")


@nox.session
def doc(session: nox.Session):
    parser = argparse.ArgumentParser("nox -s doc --")
    parser.add_argument("package", choices=os.listdir("packages"))
    parser.add_argument("action", choices=["dev", "build"])
    args, options = parser.parse_known_args(session.posargs)

    package = args.package
    action = args.action

    session.install(
        "snowballstemmer==2.2.0"
    )  # 这是 Sphinx 的依赖包，目前最新版本有问题，所以这里手动安装旧版本。
    session.install("-e", f"packages/{package}")
    session.install("jsonschema")

    if action == "dev":
        session.install("sphinx-autobuild")
        session.run(
            "sphinx-autobuild",
            *options,
            f"packages/{package}/docs",
            f"docs/_build/{package}",
        )

    if action == "build":
        session.install("sphinx")
        session.run(
            "sphinx-build",
            *options,
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


@nox.session
def testdoc(session: nox.Session):
    for package in os.listdir("packages"):
        session.notify(
            "doc",
            [
                package,
                "build",
                "-E",
                "-a",
                "--fail-on-warning",
            ],
        )


nox.options.reuse_venv = "yes"
nox.options.sessions = [
    s.__qualname__
    for s in [
        test_django_oasis,
        test_flask_oasis,
        test_starlette_oasis,
        lint,
        testdoc,
    ]
]
