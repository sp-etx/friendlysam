from enum import Enum, unique

@unique
class Resources(Enum):
    natural_gas = 1
    power = 2
    heat = 3
    msw = 4
    biofuel = 5
    heating_oil = 6