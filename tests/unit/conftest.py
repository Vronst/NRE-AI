# noqa: D100
import pytest
from data_processor.processor import factory as factory_map


class MockCityAll:  # noqa
    def __init__(self, factories: str = "all"):  # noqa
        if factories == "all":
            self.factory = list(factory_map.values())
        else:
            self.factory = []

        self.name = "testCity"


@pytest.fixture(scope="session")
def mock_city_all():  # noqa
    return MockCityAll()


@pytest.fixture(scope="session")
def mock_city_no_factory():  # noqa
    return MockCityAll(factories="None")
