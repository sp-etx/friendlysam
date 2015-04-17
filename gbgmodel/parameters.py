# -*- coding: utf-8 -*-


DEFAULTS = {
    'step' : 12, # model time units to lock per simulation step
    'time_res' : 2, # time resolution in hours
    'sched_hzn_hours' : 72, # in hours
    'tmax_hours' : 8760, # hours
    'base_year' : 2012,
    'constant_power_price' : False,
    'power_price_factor' : 1.,
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
    'mean_wind_power' : 80.e3 / 8760, # MW
    'mean_power_use' : 4407 * 10**3 / 8760, #MW, Bilaga Klimatprogrammet
    'heat_pump_Qmax' : 100, #MW
    'waste_heat_max' : 150,
    'dh_base' : 170, #MW
    'dh_rel_demand' : 1., #relative to historical
    'power_rel_demand' : 1., #relative to historical
    'fossil_allowed' : True
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


def randomize_scenario(parameters, randomizer):

    parameters = copy.deepcopy(parameters)

    parameters['sched_hzn_hours'] *= randomizer.factor(0.4)
    parameters['prices/heating_oil'] *= randomizer.factor(0.1)
    parameters['prices/bio_oil'] *= randomizer.factor(0.1)
    parameters['prices/natural_gas'] *= randomizer.factor(0.1)
    parameters['prices/wood_chips'] *= randomizer.factor(0.1)
    parameters['prices/wood_pellets'] *= randomizer.factor(0.1)
    parameters['prices/green_certificates'] *= randomizer.factor(0.1)
    parameters['certificate_quota'] *= randomizer.factor(0.2)
    parameters['mean_power_use'] *= randomizer.factor(0.05)
    parameters['mean_wind_power'] *= randomizer.factor(0.10)
    parameters['heat_pump_Qmax'] *= randomizer.factor(0.2)
    parameters['waste_heat_max'] *= randomizer.factor(0.1)
    parameters['dh_base'] *= randomizer.factor(0.1)

    return parameters


def adapt_history(
    history, ref_year=None, time_res=None, times=None, how='mean'):
    history_start = pd.datetime(ref_year, 1, 1)
    history = history.loc[history_start:]

    freq_string = str(time_res) + 'H'
    history = history.resample(freq_string, how=how)

    history = history.iloc[0:len(times)]
    history.index = times

    return history

def normalize_series(series, reference_length):
    #Normalize a series so that the first (reference_length) values have
    #series.iloc[0:reference_length].mean() == 1.
    return series / series.iloc[0:reference_length].mean()


def make_model(parameters, uncertain=None):
    if not uncertain:
        uncertain = DummyRandomizer()

    parameters['sched_hzn'] = parameters['sched_hzn_hours'] /  parameters['time_res']

    model = fs.models.MyopicDispatchModel(
        t0=parameters['t0'],
        horizon=parameters['sched_hzn'],
        step=parameters['step'])

    # Historical data range
    history_length = parameters['tmax'] + parameters['sched_hzn'] + 1
    times = np.arange(1, history_length+1, dtype=int)

    heat_history = adapt_history(
        essim.data.heat.get_history('essim/data/heat_plants_3.json'),
        parameters['base_year'],
        times=times,
        time_res=parameters['time_res'],
        how='sum')

    power_history_SE = adapt_history(
        essim.data.power.load_history(),
        parameters['base_year'],
        times=times,
        time_res=parameters['time_res'],
        how='sum')

    power_price_history = adapt_history(
        essim.data.nordpool.load_history()['SE2'],
        parameters['base_year'],
        times=times,
        time_res=parameters['time_res'],
        how='mean')


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
            name = u'Rya CHP',
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
            name = u'Högsbo CHP',
            eta = uncertain.relative(0.85, 0.05),
            alpha = uncertain.relative(0.8, 0.05),
            Fmax = uncertain.relative(34 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_CHP']))

    model.add_part(
        Boiler(
            name = u'Sävenäs boiler A',
            eta = uncertain.relative(1.03, 0.05),
            Fmax = uncertain.relative(89 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = u'Sävenäs boiler B',
            eta = 0.89 * randomizer.factor(0.05),
            Fmax = uncertain.relative(89 * parameters['time_res'], 0.1),
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = u'Rosenlund boiler B',
            eta = uncertain.relative(0.93, 0.05),
            Fmax = 155 * parameters['time_res'],
            fuel = Resources.natural_gas,
            fuel_cost = parameters['prices/natural_gas'] + parameters['tax_NG_heat']))

    model.add_part(
        Boiler(
            name = u'Rosenlund boiler A',
            eta = 0.9 * randomizer.factor(0.05),
            Fmax = uncertain.relative(465 * parameters['time_res'], 0.1),
            fuel = Resources.heating_oil,
            fuel_cost = parameters['prices/heating_oil'] + parameters['tax_oil_heat']))

    model.add_part(
        Boiler(
            name = u'Rya boiler',
            eta = uncertain.relative(0.87, 0.05),
            Fmax = uncertain.relative(115 * parameters['time_res'], 0.1),
            fuel = Resources.biofuel,
            fuel_cost = parameters['prices/wood_pellets'])) #pellets + lite naturgas

    model.add_part(
        Boiler(
            name = u'Tynnered boiler',
            eta = uncertain.relative(0.9, 0.05),
            Fmax = uncertain.relative(22 * parameters['time_res'], 0.2),
            fuel = Resources.heating_oil,
            fuel_cost = parameters['prices/heating_oil'] + parameters['tax_oil_heat']))

    model.add_part(
        Boiler(
            name = u'Angered boiler',
            eta = 0.9 * randomizer.factor(0.05),
            Fmax = uncertain.relative(137 * parameters['time_res'], 0.1),
            fuel = Resources.biofuel,
            fuel_cost = parameters['prices/bio_oil']))

    model.add_part(
        Import(
            name = u'Industrial waste heat',
            resource = Resources.heat,
            max_import = parameters['waste_heat_max'] * parameters['time_res'],
            max_export = 0,
            cost = 0))

    model.add_part(
        HeatPump(
            name = u'Rya heat pump',
            COP = uncertain.absolute(3.3, 0.2),
            Qmax = parameters['heat_pump_Qmax'] * parameters['time_res'],
            cost = (parameters['certificate_quota'] * 
                parameters['prices/green_certificates'] +
                parameters['electricity_tax'])))

    # Q_t = b + h_t
    # Q*_t = b + h*_t
    # require that
    # sum_t Q*_t = T * b + sum_t h*_t = k * sum_t Q_t = k * b * T + k * sum_t h_t
    # and require that
    # h*_t = c * h_t
    # ==>
    # b * T * (1 - k) = sum_t (h_t - h*_t) = (k - c) * sum_t h_t
    # ==>
    # c = k - b * T * (1 - k) / sum_t h_t = k - b * (1 - k) / mean(h_t)

    k = parameters['dh_rel_demand']
    b = parameters['dh_base'] * parameters['time_res']
    h = heat_history.sum(axis=1) - b
    c = k - b * (1. - k) / h.mean()
    dh_demand = b + c * h

    model.add_part(
        Consumer(
            name = u'District heating demand',
            resource = Resources.heat,
            demand = dh_demand))


    #Power use in heat pumps
    heat_pump_use = heat_history[u'Rya heat pump'] / rya_HP_COP #MW averages

    #Power demand excluding heat pump use
    power_use_SE = power_history_SE[u'Total förbrukning']
    city_power_demand = (parameters['time_res'] * parameters['mean_power_use'] * 
        normalize_series(power_use_SE, parameters['tmax'])
        - heat_pump_use) * parameters['power_rel_demand']

    model.add_part(
        Consumer(
            name = u'Power demand',
            resource = Resources.power,
            demand = city_power_demand))

    
    if parameters['constant_power_price']:
        power_price = (
            (power_use_SE * power_price_history).sum() /
            power_use_SE.sum()) * parameters['power_price_factor']
    else:
        power_price = power_price_history * parameters['power_price_factor']

    model.add_part(
        Import(
            name = u'Power import',
            resource = Resources.power,
            cost = power_price))

    wind_history_SE = power_history_SE[u'Vindkraft']
    wind_power_delivery = (parameters['time_res'] * parameters['mean_wind_power'] * 
        normalize_series(wind_history_SE, parameters['tmax']))

    model.add_part(
        Import(
            name = u'Wind power',
            resource = Resources.power,
            cost = 0,
            amount = wind_power_delivery))

    return elements

        