
from math import radians, sin, cos, sqrt, asin
import random

class Location:
  def __init__(self, idnum, lat, lon, mass):
    self.idnum = idnum
    self.lat = lat
    self.lon = lon
    self.mass = mass
  def __str__(self):
    return "id:"+str(self.idnum)+", lat:"+str(self.lat)+", lon:"+str(self.lon)+", mass:"+str(self.mass)
  def __repr__(self):
    return "<id:"+str(self.idnum)+", lat:"+str(self.lat)+", lon:"+str(self.lon)+", mass:"+str(self.mass) + ">"


startingLocation = Location(0, 68.073611, 29.315278, 0)
locations = []
masslimit = 10000000 # grams

def flatten(listoflists):
    return [item for sublist in listoflists for item in sublist]

def haversine(lat1, lon1, lat2, lon2):
  # calculate shortest great-circle distance between two lat/lon pairs 
  R = 6378 # Earth radius in kilometers
  dLat = radians(lat2 - lat1)
  dLon = radians(lon2 - lon1)
  lat1 = radians(lat1)
  lat2 = radians(lat2)
  a = sin(dLat/2)**2 + cos(lat1)*cos(lat2)*sin(dLon/2)**2
  c = 2*asin(sqrt(a)) 
  return R * c

def distcalc(l1, l2):
  return haversine(l1.lat, l1.lon, l2.lat, l2.lon)

def triplength(locations):
  loc = startingLocation
  distance = 0
  for l in locations:
    dist = distcalc(loc, l)
    distance += dist
    loc = l
  distance += distcalc(loc, startingLocation)
  return distance

def parseList():
  with open("triplist.txt") as triplist:
    trips = triplist.readlines()
  for trip in trips:
    entries = [x.strip() for x in trip.split(';')]
    locations.append(Location(int(entries[0]), float(entries[1]), float(entries[2]), int(entries[3])))
  return locations

def generateTriplists(locs):
    # randomly shuffle the locs
    random.shuffle(locs)
    index = 0
    trip = 0
    triplists = [[]]
    totalmass = 0
    nextmass = locs[0].mass
    while(index < len(locs) - 1):
        while(totalmass + nextmass < masslimit):
            triplists[trip].append(locs[index])
            totalmass += locs[index].mass
            if index + 1 >= len(locs):
                break
            index += 1
            nextmass = locs[index].mass
        if index + 1 >= len(locs):
            break
        triplists.append([])
        trip += 1
        totalmass = 0
    for trip in triplists:
        trip.append(startingLocation)
        trip.reverse()
        trip.append(startingLocation)
        trip.reverse()
    return triplists

def evaluate(triplists):
    distance = 0
    for trip in triplists:
        distance += triplength(trip)
    return distance

def mutate(triplists, degree):
    for trip in triplists:
        if random.random() < degree:
            random.shuffle(trip)

def crossover(triplist1, triplist2):
    # print("Crossover")
    tls1 = triplist1
    tls2 = triplist2
    random.shuffle(tls1)
    random.shuffle(tls2)
    lists = [tls1, tls2]
    activelist = 0
    child1 = []
    # build the first child
    index = 0
    while index < max(map(len,lists)):
        if index >= len(lists[activelist]):
            activelist = not activelist
        child1.append(lists[activelist][index])
        activelist = not activelist
        index = index + 1
    # print("child_cleanup")
    child1,seenvals = removeDuplicates(child1)
    child1 = fillEmpties(child1)
    activelist = 1
    child2 = []
    # build the second child
    index = 0
    while index < max(map(len,lists)):
        if index >= len(lists[activelist]):
            activelist = not activelist
        child2.append(lists[activelist][index])
        activelist = not activelist
        index = index + 1
    # print("child_cleanup")
    child2,seenvals = removeDuplicates(child2)
    child2 = fillEmpties(child2)
    return(child1,child2)

def removeDuplicates(triplist):
    seen = []
    for trip in triplist:
        for loc in trip:
            if loc in seen:
                trip.remove(loc)
            else:
                seen.append(loc)
    # print "seen"
    # print seen
    return triplist,seen

def fillEmpties(triplist):
    fillwith = [l for l in locations if l not in flatten(triplist)]
    for loc in fillwith:
        allocated = False
        for trip in triplist:
            tripmass = sum([l.mass for l in trip])
            if loc.mass < (masslimit - tripmass):
                trip.append(loc)
                allocated = True
                break
        if not allocated:
            triplist.append([loc])
    return triplist



# tls1 = generateTriplists(locations)
# tls2 = generateTriplists(locations)


def run():
    num_units = 100 # should be divisible by 4
    num_generations = 20
    locations = parseList()
    units = [generateTriplists(locations) for i in range(num_units)]
    best_unit_score = []
    generation_fitness = []
    for gen in range(num_generations):
        # make a weighted spinner so that the best options are more likely to mate, and the worst are less likely.
        # if an option is twice as good as the worst option, it should have 2x as much probability mass.
        indexes_to_mate = []
        new_units = []
        evaluations = [(u,ev) for u,ev in enumerate([evaluate(u) for u in units])]
        generation_evaluation = sum([e[1] for e in evaluations])
        print("generation_evaluation")
        print(generation_evaluation)

        generation_fitness.append(generation_evaluation)
        max_val = max([e[1] for e in evaluations])
        min_val = min([e[1] for e in evaluations])
        best_unit_score.append(min_val)
        # print("min_val")
        ratios = [min_val/float(e[1]) for e in evaluations]
        total = sum(ratios)
        slices = [r/total for r in ratios]

        def running_sum(a):
            total = 0
            for item in a:
                total += item
                yield total

        wheel = list(running_sum(ratios))
        # print("Wheel_generated")
        num_spins = num_units/2
        for s in range(num_spins):
            spin = random.random()
            n = 0
            while(spin > wheel[n]):
                n += 1
            indexes_to_mate.append(n)
        # print("spins spun")
        for m in range(len(indexes_to_mate)/2):
            c1,c2 = crossover(units[m],units[m+1])
            mutate(c1,.001)
            mutate(c2,.001)
            new_units.append(c1)
            new_units.append(c2)
        units = new_units
    print("Summary:")
    print("best_unit_score:"+ str(best_unit_score))
    print("generation_fitness:"+ str(generation_fitness))


if __name__ == "__main__":
    run()



