import math
import json
from copy import deepcopy


ONE_OPT = 25
START_FROM = "Vienna"


class Destination:
    # Class created specifically for destination including info
    # about cost of housing, every possible flight and days of stay
    cost_per_night = 0
    flights = []
    minimum_days = 0
    optimum_days = 0
    maximum_days = 0

    def __init__(self, cost, flights, minimum_days, optimum_days, maximum_days):
        self.cost_per_night = cost
        self.flights = flights
        self.minimum_days = minimum_days
        self.optimum_days = optimum_days
        self.maximum_days = maximum_days

    def __str__(self) -> str:
        return 'night {}, flights {}, minim {}, optim {}, maxim {}'.\
            format(self.cost_per_night, self.flights, self.minimum_days,
                   self.optimum_days, self.maximum_days)


class Trip:
    # Class for whole trip
    # price -> price of the trip (including flights and housing)
    # optimal -> difference in days from optimal stays in the countries
    #           (optimal value is 0, staying one day longer then one day shorter counts as 2, not 0)
    # flights -> times of the flights in selected order of visitations
    price = 0
    optimum = 0
    flights = []

    def __init__(self, price, flight):
        self.price = price
        self.optimum = 0
        self.flights = [flight]

    def __str__(self) -> str:
        return 'price {}, optimal {}, flights {}'.format(self.price, self.optimum, self.flights)

    def add_flight(self, destination: Destination, flight):
        days = (int(flight) - int(self.flights[-1]))
        self.price += days * destination.cost_per_night + \
            destination.flights[flight]['cost']
        self.optimum += abs(days - destination.optimum_days)
        self.flights.append(flight)


def flights_to_trips(dest):
    # Converting dict format of flights to Trip classes
    # input -> dest -> dict of flights from json file
    # output -> res -> dict of Trip classes
    res = dict()
    for dep in dest['departures'].keys():
        res[dep] = Trip(price=dest['departures'][dep]
                        ['cost'], flights=dep)

    return res


def optimal_days(destination, days):
    # Loading info about days of given country from optimal_days JSON file
    for dest in days:
        if dest['name'] == destination:
            return dest['minimum'], dest['optimum'], dest['maximum']

    raise RuntimeError(
        'Country {} is not in JSON file with optimal days'.format(destination))


def create_dest_dictionary(dest_json, opt_days_json):
    # creating core of the dataset
    # input ->  dest_json -> raw json of destinations including pricing and flights
    #           opt_days_json -> raw json of optimal days for each country
    # output -> dictionary with keys as name of the country and value as Destination
    #           class with all the info
    res = dict()
    for dest in dest_json:
        minimum, optimum, maximum = optimal_days(dest['name'], opt_days_json)
        res[dest['name']] = Destination(
            dest['cost_per_night'], dest['departures'], minimum, optimum, maximum)

    return res


def create_trips(departures):
    res = dict()
    for flight in departures.keys():
        res[flight] = Trip(departures[flight]['cost'], flight)

    return res


def calculate_trips(trips, dest_dict):
    res = deepcopy(trips)
    for country in dest_dict.keys():
        new_trips = dict()
        dest = dest_dict[country]

        for until in dest.flights.keys():
            departures = []

            # selecting all departures for given trip in given day span
            for since in list(res.keys()):
                if dest.minimum_days <= int(until) - int(since) <= dest.maximum_days:
                    departures.append(since)

            if departures == []:
                continue

            best = deepcopy(res[departures[0]])
            best.add_flight(dest, until)

            for dep in departures[1:]:
                tmp = deepcopy(res[dep])
                tmp.add_flight(dest, until)
                tmp_opt = 0 if tmp.price < best.price else tmp.price - best.price
                if tmp_opt // ONE_OPT + tmp.optimum < best.optimum:
                    best = tmp

            new_trips[until] = best

        res = new_trips

    return res


def choose_ideal(trips):
    dates = list(trips.keys())
    best = trips[dates[0]]

    for pos in dates[1:]:
        tmp = trips[pos]
        tmp_opt = 0 if tmp.price < best.price else tmp.price - best.price
        if tmp_opt // ONE_OPT + tmp.optimum < best.optimum:
            best = tmp

    print(str(best))


def algorithm(flights_filename: str, days_filename: str) -> None:
    # creating dictionary of flights from json file
    with open(flights_filename, encoding='utf-8') as f:
        dest_json = json.load(f)['destinations']

    # creating dictionary of optimum flights from json file via optimal_days function
    with open(days_filename, encoding='utf-8') as g:
        opt_days_json = json.load(g)['days']

    dest_dict = create_dest_dictionary(dest_json, opt_days_json)

    trips = create_trips(dest_dict[START_FROM].flights)
    del dest_dict[START_FROM]
    res = calculate_trips(trips, dest_dict)

    for trip in res.keys():
        print(str(res[trip]))

    print('\noptimal')
    choose_ideal(res)


algorithm('flights.json', 'optimal_days.json')
