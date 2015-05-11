# -*- coding: utf-8 -*-

DEFAULTS = {
    'step' : 12, # model time units to lock per simulation step
    'time_res' : 2, # time resolution in hours
    'sched_hzn_hours' : 72, # in hours
    'tmax_hours' : 8760, # hours
    'tax_NG_CHP' : 24, #SEK/MWh(LHV)
    'tax_NG_heat' : 250, #SEK/MWh(LHV)
    'tax_oil_heat' : 300, #SEK/MWh(LHV)
    'prices/heating_oil' : 500, #SEK/MWh(LHV)
    'prices/bio_oil' : 500, #SEK/MWh(LHV)
    'prices/natural_gas' : 280, #SEK/MWh(LHV)
    'prices/wood_chips' : 200, #SEK/MWh(LHV)
    'prices/wood_pellets' : 320, #SEK/MWh(LHV)
    'prices/green_certificates' : 200, #SEK/MWh
    'electricity_tax' : 180, #SEK/MWh
    'certificate_quota' : 0.15,
    'power_demand' : data.power_demand(),
    'wind_power' : data.wind_power(),
    'dh_demand' : data.district_heating_demand()
}

def get_custom(**kwargs):
    parameters = copy.deepcopy(DEFAULTS)
    parameters.update(kwargs)
    return parameters


class Randomizer(object):
    """docstring for Randomizer"""
    def __init__(self, seed):
        super().__init__()
        self._random_state = np.random.RandomState(seed)


    def relative(self, value, *args, **kwargs):
        return value * self.factor(*args, **kwargs)


    def absolute(self, value, *args, **kwargs):
        return value + self.term(*args, **kwargs)


    def factor(self, a, b=None):
        if b is None:
            low, high = 1 - a, 1 + a
        else:
            low, high = a, b

        return self._random_state.uniform(low, high)


    def term(self, a, b=None):
        if b is None:
            low, high = -a, a
        else:
            low, high = a, b
        return self._random_state.uniform(low, high)


class DummyRandomizer(object):
    """docstring for DummyRandomizer"""

    def _do_nothing(value, *args, **kwargs):
        return value
    
    relative = _do_nothing
    absolute = _do_nothing
    
    def factor(self, *args, **kwargs):
        return 1

    def term(self, *args, **kwargs):
        return 0        


def make_model(parameters, seed=None):
    uncertain = DummyRandomizer() if seed is None else Randomizer(seed)

    parameters['sched_hzn'] = parameters['sched_hzn_hours'] /  parameters['time_res']

    model = fs.models.MyopicDispatchModel(
        t0=parameters['t0'],
        horizon=parameters['sched_hzn'],
        step=parameters['step'])

    renova = LinearCHP(
            name='Renova CHP',
            eta=uncertain.relative(0.95, 0.03),
            alpha=uncertain.relative(0.14, 0.1),
            fuel=Resources.msw,
            fuel_cost=0)

    renova.constraints += (
        lambda t: renova.production[Resources.heat](t) == heat_history['Renova CHP'](t))
    model.add_part(renova)

    model.add_part(
        LinearCHP(
            name = 'Rya CHP',
            eta = uncertain.relative(0.925, 0.03),
            alpha = uncertain.relative(0.86, 0.05),
            Fmax = uncertain.relative(600 * parameters['time_res'], 0.05),
            Fmin = uncertain.relative(600 * 0.20 * parameters['time_res'], 0.3),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_CHP']))

    
    # This is not a good formulation
    certificate_income = (eta * alpha / (1 + alpha)) * parameters['prices/green_certificates']
    model.add_part(
        LinearSlowCHP(
            name = 'Sävenäs CHP',
            eta = uncertain.relative(1.07, 0.05),
            alpha = uncertain.relative(0.08, 0.2),
            Fmax = uncertain.relative(130 * parameters['time_res'], 0.1),
            Fmin = uncertain.relative(130 * 0.3 * parameters['time_res'], 0.5),
            startup_time = int(np.round(uncertain.absolute(6, -4, 6) / parameters['time_res'])), #hours
            fuel = Resources.biofuel, #flis + lite bioolja
            fuel_cost = parameters['prices/wood_chips'] - certificate_income))

    model.add_part(
        LinearCHP(
            name = 'Högsbo CHP',
            eta = uncertain.relative(0.85, 0.05),
            alpha = uncertain.relative(0.8, 0.05),
            Fmax = uncertain.relative(34 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_CHP']))

    model.add_part(
        Boiler(
            name = 'Sävenäs boiler A',
            eta = uncertain.relative(1.03, 0.05),
            Fmax = uncertain.relative(89 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = 'Sävenäs boiler B',
            eta = uncertain.relative(0.89, 0.05),
            Fmax = uncertain.relative(89 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = 'Rosenlund boiler B',
            eta = uncertain.relative(0.93, 0.05),
            Fmax = 155 * parameters['time_res'],
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = 'Rosenlund boiler A',
            eta = uncertain.relative(0.9, 0.05),
            Fmax = uncertain.relative(465 * parameters['time_res'], 0.1),
            fuel = Resources.heating_oil,
            fuel_cost = parameters['prices/heating_oil'] + parameters['tax_oil_heat']))

    model.add_part(
        Boiler(
            name = 'Rya boiler',
            eta = uncertain.relative(0.87, 0.05),
            Fmax = uncertain.relative(115 * parameters['time_res'], 0.1),
            fuel = Resources.biofuel,
            fuel_cost = parameters['prices/wood_pellets'])) #pellets + lite naturgas

    model.add_part(
        Boiler(
            name = 'Tynnered boiler',
            eta = uncertain.relative(0.9, 0.05),
            Fmax = uncertain.relative(22 * parameters['time_res'], 0.2),
            fuel = Resources.heating_oil,
            fuel_cost = parameters['prices/heating_oil'] + parameters['tax_oil_heat']))

    model.add_part(
        Boiler(
            name = 'Angered boiler',
            eta = uncertain.relative(0.9, 0.05),
            Fmax = uncertain.relative(137 * parameters['time_res'], 0.1),
            fuel = Resources.biofuel,
            fuel_cost = parameters['prices/bio_oil']))

    model.add_part(
        Import(
            name = 'Industrial waste heat',
            resource = Resources.heat,
            max_import = uncertain.relative(150, 0.2) * parameters['time_res'],
            max_export = 0,
            price = 0))

    model.add_part(
        HeatPump(
            name = 'Rya heat pump',
            COP = uncertain.absolute(3.3, 0.2),
            Qmax = uncertain.relative(100, 0.2) * parameters['time_res'],
            power_cost = (parameters['certificate_quota'] * 
                parameters['prices/green_certificates'] +
                parameters['electricity_tax'])))

    model.add_part(
        Consumer(
            name = 'District heating demand',
            resource = Resources.heat,
            demand = parameters['dh_demand']))

    model.add_part(
        Consumer(
            name = 'Power demand',
            resource = Resources.power,
            demand = power_demand))

    model.add_part(
        Import(
            name = 'Power import',
            resource = Resources.power,
            cost = power_price))

    model.add_part(
        Import(
            name = 'Wind power',
            resource = Resources.power,
            cost = 0,
            amount = wind_power))

    return elements

        