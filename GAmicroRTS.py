#start_imports
from random import Random
from time import time
from math import cos
from math import pi
from inspyred import ec
from inspyred.ec import terminators
import subprocess
import pandas as pd
#end_imports


def generate_agent(random, args):
    size = 10 # number of parameters

    agent = [random.random() for i in range(size)]
    agent[3] = random.randint(1,10) # number of workers
    agent[4] = random.randint(1,20) # attacking workers

    return agent


def evaluate_agent(candidates=None, args=None):
    fitness = []
    class_path = 'bin/' +\
      ':lib/hamcrest-all-1.3.jar:' +\
      'lib/jdom.jar:lib/junit-4.12.jar:' +\
      'lib/minimal-json-0.9.4.jar:lib/weka.jar:' +\
      '../MicroRTS/MicroRTS.jar'

    for cs in candidates:
        result_file = subprocess.run(['java', '-cp', class_path, 'tournament.EvaluationTournament'] + [str(c) for c in cs], capture_output=True, text=True)

        # Read CSV file
        print(result_file.stderr)
        df = pd.read_csv(result_file.stdout)
        offset = 14
        nAIs = 1
        nOpponentAIs = 2
        nMaps = 2
        nIter = 2
        wins_row_idx = (offset + nMaps + nAIs + nOpponentAIs + (nOpponentAIs * nMaps * nIter)) - 2 # Minus 2 because of the column label and 0 indexing
        ties_row_idx = wins_row_idx + 2

        # check number of rows
        if len(df) >= ties_row_idx:
            wins_row = df.iloc[wins_row_idx]
            ties_row = df.iloc[ties_row_idx]

            # convert to numeric and sum the values 
            if (nOpponentAIs > 1):
                ind_fitness = sum(float(wins) for wins in wins_row[0].split('\t') if wins)
                ind_fitness += sum(float(ties) for ties in ties_row[0].split('\t') if ties) * 0.5
                fitness.append(ind_fitness)
            else:
                fitness.append(int(wins_row) + 0.5*int(ties_row))

    return fitness


# start_main
rand = Random()
rand.seed(int(time()))
ea = ec.GA(rand)
ea.terminator = terminators.evaluation_termination
ea.observer = ec.observers.file_observer
ea.variator = ec.variators.uniform_crossover

evaluations = 20
pop_size = 10

inicio = time()
final_pop = ea.evolve(generator=generate_agent,
                      evaluator=evaluate_agent,
                      pop_size=pop_size,
                      seeds = [[0.2, 0.82, 0.85, 5, 0, 0.7, 0.4, 0, 0.12, 0.25],
                               [0.2, 0.95, 0.9, 3, 0, 0.3, 0.4, 0.3, 0.08, 0.1],
                               [0.2, 1, 0.8, 3, 20, 0, 0, 0, 0.08, 0.1]],
                      maximize=True,
                      bounder=ec.Bounder([0, 0, 0, 1, 1, 0, 0, 0, 0, 0], 
                                        [1, 1, 1, 10, 20, 1, 1, 1, 1, 1]),
                      max_evaluations=evaluations)
fin = time()

# Sort the popoulation. Best individual at index 0.
final_pop.sort(reverse=True)

# write data
timestamp = time()
file = open("stats_ga " + str(timestamp) + ".txt", 'a')
file.write(str(fin-inicio) + " seconds employed\n")
file.write(str(evaluations) + " evaluations\n")
file.write(str(pop_size) + " pop size\n")
file.write("Best individual\n")
file.write(str(final_pop[0]) + "\n")
file.close()

pd.DataFrame(final_pop).to_csv("population" + str(timestamp) + ".csv")

# print data
print(str(fin-inicio) + " seconds employed")
print(str(evaluations) + " evaluations")
print(str(pop_size) + " pop size")
print("Best individual")
print(str(final_pop[0]))
#end_main
