# noqa: D100
from types import SimpleNamespace

import pytest


def make_city(  # noqa
    name="test", connections=None, fee=0, commodities=None, **kwargs
):  # noqa
    if not connections:
        connections = []
    if not commodities:
        commodities = {}
    return SimpleNamespace(
        name=name,
        connections=connections,
        fee=fee,
        commodities=commodities,
        **kwargs,
    )


@pytest.fixture(scope="session")
def city_factory():  # noqa
    return make_city


# class MockCityAll:  # noqa
#     def __init__(self, factories: str = "all"):  # noqa
#         if factories == "all":
#             self.factory = list(factory_map.values())
#         else:
#             self.factory = []

#         self.name = "testCity"

#         self.connections = {}
#         for number in range(5):
#             for x in range(100, 49, -25):
#                 self.connections["city" + str(number)] = {
#                     "fee": x,
#                     "commodities"
#                 }
#         self.connections: dict= {
#             'city1': {'fee': 100},
#             'city2': {'fee': 75},
#             'city3': {'fee': 50}
#         }

#     @property
#     def cities(self) -> dict:  # noqa
#         return self.connections

# @pytest.fixture(scope="session")
# def mock_city_all():  # noqa
#     return MockCityAll()


# @pytest.fixture(scope="session")
# def mock_city_no_factory():  # noqa
#     return MockCityAll(factories="None")
