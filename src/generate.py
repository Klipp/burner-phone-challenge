import random
import math
import uuid
import csv

### ASSUMPTIONS (which should change, TODO) ###
# 1. Everyone only has one phone at a time
# 2. Highest resolution is an hour, only one "call" can happen per hour
# 3. No day/night cycle

### Parameters ###

# total number of cells for the area of interest
num_cells = 1000

# total number of people call records are collected for
num_people = 1000

# time is in hours, starting from 0
# so, if end time is 48, the generated data spans two days
end_time = 30 * 24

# on average, people change numbers every... (in hours)
change_numbers_every = 365 * 24 * 3

people = []

### Utility Functions ###
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

# modified from https://stackoverflow.com/questions/26226801/making-random-phone-number-xxx-xxx-xxxx
def phone_number_generator():
    already_used = []
    while True:
        p=list('0000000000')
        p[0] = str(random.randint(1,9))
        for i in [1,2,6,7,8]:
            p[i] = str(random.randint(0,9))
        for i in [3,4]:
            p[i] = str(random.randint(0,8))
        if p[3]==p[4]==0:
            p[5]=str(random.randint(1,8))
        else:
            p[5]=str(random.randint(0,8))
        n = list(range(10))
        if p[6]==p[7]==p[8]:
            n = (i for i in n if i!=p[6])
        #import pdb; pdb.set_trace()
        p[9] = random.choice(list(n))
        p = ''.join([str(x) for x in p])
        number = p[:3] + '-' + p[3:6] + '-' + p[6:]
        if number not in already_used:
            already_used.append(number)
            yield number

random_phone_number = phone_number_generator()


class Person():
    """ a single person, who has one or more cell phones, each with a unique
    cell phone number """
    def __init__(self):
        # how can we uniquely identify them?
        self._uuid = uuid.uuid4()
        # NOTE using this would be cheating :)

        # number of contacts they usually call
        self.num_contacts = math.ceil(random.normalvariate(10, 3))
        self.num_contacts = clamp(self.num_contacts, 1, 200)

        # who do they usually call?
        self.contacts = []

        # how habitual are they in their contacts?
        # 1 = always contacts the same set of contacts
        # 0 = completely uniform random contact for each call
        self.contact_regularity = random.normalvariate(.95, .01)

        # how often do they call people?
        # mean of 3 = 1/3 chance for average person to make call any given hour
        self.cell_usage = random.normalvariate(3,.30)
        if self.cell_usage < 0:
            self.cell_usage = .001

        # number of locations they usually call from
        self.num_cells = math.ceil(random.normalvariate(10, 3))
        self.num_cells = clamp(self.num_cells, 1, 200)

        # what cells (locations) do they commonly call from?
        self.cells = random.sample(range(num_cells), self.num_cells)

        # how habitual are they in their locations?
        # 1 = always uses the same set of locations
        # 0 = completely uniform random cell for each call
        self.cell_regularity = random.normalvariate(.8, .05)

        # how frequently (on average) does someone change phones?
        self.number_switch_frequency = 0
        while self.number_switch_frequency < 24:
            # stipulate that nobody change numbers more than once per day
            frequency = 1.0/change_numbers_every
            self.number_switch_frequency = random.expovariate(frequency)

        prob_per_hour = 1/self.number_switch_frequency
        # everybody "switches" at t=0
        self.switch_times = [0]
        for hour in range(end_time):
            if random.random() < prob_per_hour:
                self.switch_times.append(hour)

        self.numbers = []
        for time in self.switch_times:
            self.numbers.append(CellNumber(self))

        assert len(self.switch_times) == len(self.numbers)

    def pick_contacts(self, cell_numbers):
        """ given a full list of cell numbers, pick which numbers this person
        usually calls """
        self.contacts = random.sample(cell_numbers, self.num_contacts)

    def __repr__(self):
        return "<Person contacts:{} cells:{} switch_frequency:{}" \
               "switch_times:{}>".format(
                  len(self.contacts),
                  len(self.cells),
                  self.number_switch_frequency,
                  len(self.switch_times)
                  )


class CellNumber():
    """ Describes a single cell number, which (usually) has a number of call
    records associated with it. A person could have one number, or more """

    def __init__(self, person):
        self.uuid = next(random_phone_number)
        self.person = person
        self.call_records = []

    def generateRecords(self, cell_numbers):
        for hour in range(end_time):
            if random.random() < 1/self.person.cell_usage:
                # they made a call/texted/etc. in this hour
                self.generateRecord(hour, cell_numbers)

    def generateRecord(self, time, cell_numbers):
        """ generates a call record from a random location to a random contact
        at a specified time """

        # choose a location
        if random.random() < self.person.cell_regularity:
            # in one of their cells
            location = random.choice(self.person.cells)
        else:
            # outside of one of their usual cells
            location = random.randrange(num_cells)

        # choose a contact
        if random.random() < self.person.contact_regularity:
            # calling a regular contact
            contact = random.choice(self.person.contacts)
        else:
            # venturing to call someone totally new
            contact = random.choice(cell_numbers)

        # assemble call record, store in self.call_records
        self.call_records.append({
            'cell':location,
            'from': self.uuid,
            'to': contact.uuid,
            'time': time
            })


if __name__ == "__main__":
    for x in range(num_people):
        people.append(Person())

    # build a list of all cell numbers
    cell_numbers = []
    for person in people:
        for cell_number in person.numbers:
            cell_numbers.append(cell_number)

    # pick each person's favored contacts from the numbers
    for person in people:
        person.pick_contacts(cell_numbers)

    # generate call records for each number
    for cell_number in cell_numbers:
        cell_number.generateRecords(cell_numbers)

    # put all of the call records in one place
    all_records = []
    for person in people:
        for number in person.numbers:
            all_records.extend(number.call_records)

    # sort the call records by time
    all_records = sorted(all_records, key=lambda k: k['time'])

    # write out all of the call records
    with open('call_records.csv', 'w') as csvfile:
        fieldnames = ['time', 'cell', 'from', 'to']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in all_records:
            writer.writerow(row)

    print("[*] Call record data written to call_records.csv")

    # build a dict mapping numbers to people (the solutions!)
    solutions = []
    for person in people:
        for number,time in zip(person.numbers, person.switch_times):
            solutions.append({
                'person': person._uuid,
                'number': number.uuid,
                'switch_time': time
                })


    # write out the "who has a number when" solutions
    with open('solutions.csv', 'w') as csvfile:
        fieldnames = ['person', 'number', 'switch_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in solutions:
            writer.writerow(row)

    print("[*] Solutions written to solutions.csv")

    try:
        import networkx as nx

        G=nx.DiGraph()

        for record in all_records:
            G.add_edge(str(record['from']), str(record['to']), time=record['time'], cell=record['cell'])

        nx.write_gexf(G, 'call_records.gexf')
        print("[*] Call record data written to call_records.gexf")
    except ImportError:
        print("[!] NetworkX library not found, skipping graph export.")


    # TODO shuffle/sort by time and export records

