from pathlib import Path

from cleo.testers.application_tester import ApplicationTester
from poetry.console.application import Application
from poetry.factory import Factory

fixtures_dir = Path(__file__).parent / "fixtures"


def test_poetry_loads_plugin():
    poetry = Factory().create_poetry(fixtures_dir / "sample_project")
    app = Application()
    app._poetry = poetry
    tester = ApplicationTester(app)
    tester.execute()
    assert tester.status_code == 0
