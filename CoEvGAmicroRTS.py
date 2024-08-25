#start_imports
from random import Random
from time import time
import os
import csv
from inspyred import ec
from inspyred.ec import terminators
from inspyred.ec import evaluators
import subprocess
import pandas as pd
#end_imports


def generate_agent(random, args):
    size = 10 # number of parameters

    agent = [random.random() for i in range(size)]
    agent[3] = random.randint(1,10) # number of workers
    agent[4] = random.randint(1,20) # attacking workers

    return agent


def evaluate_agents(candidates, args=None):
    csvPath = "myAgents.csv"
    fitness = []
    class_path = 'bin/' +\
      ':lib/hamcrest-all-1.3.jar:' +\
      'lib/jdom.jar:lib/junit-4.12.jar:' +\
      'lib/minimal-json-0.9.4.jar:lib/weka.jar:' +\
      '../MicroRTS/MicroRTS.jar'
    
    # Verificar si el archivo ya existe
    if os.path.isfile(csvPath):
        # Si existe, agregar un número al nombre para crear un nuevo archivo
        base, extension = os.path.splitext(csvPath)
        counter = 1
        new_filename = f"{base}_{counter}{extension}"
        while os.path.isfile(new_filename):
            counter += 1
            new_filename = f"{base}_{counter}{extension}"
        csvPath = new_filename

    # Crear el archivo CSV
    with open(csvPath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(candidates)

    result_file = subprocess.run(['java', '-cp', class_path, 'tournament.CoEvEvaluationTournament'] + [csvPath], 
                                 capture_output=True, text=True)

    # Read CSV file
    df = pd.read_csv(result_file.stdout)
    offset = 14
    nAIs = len(candidates)
    nMaps = 3
    nIter = 2
    wins_row_idx = (offset + nMaps + nAIs + (nAIs * nAIs * nMaps * nIter)) - 1 # Minus 2 because of the column label and 0 indexing
    ties_row_idx = wins_row_idx + 1 + nAIs

    # check number of rows
    if len(df) >= ties_row_idx:
        for _ in range(nAIs):
            wins_row = df.iloc[wins_row_idx]
            ties_row = df.iloc[ties_row_idx]

            # convert to numeric and sum the values 
            if (nAIs > 1):
                ind_fitness = sum(float(wins) for wins in wins_row[0].split('\t') if wins)
                ind_fitness += sum(float(ties) for ties in ties_row[0].split('\t') if ties) * 0.5
            else:
                ind_fitness = int(wins_row) + 0.5*int(ties_row)

            fitness.append(ind_fitness)

            wins_row_idx = wins_row_idx + 1
            ties_row_idx = ties_row_idx + 1
    else:
        fitness.append([0] * nAIs)
        
    return fitness


# start_main
rand = Random()
rand.seed(int(time()))
ea = ec.GA(rand)
# ea.selector = ec.selectors.tournament_selection # using default rank_selection
ea.terminator = [terminators.evaluation_termination, terminators.time_termination]
ea.observer = ec.observers.file_observer
ea.replacer = ec.replacers.plus_replacement # ec.replacers.steady_state_replacement


inicio = time()

# same parameters as in "Optimizing Hearthstone agents using an evolutionary algorithm"
evaluations = 20
pop_size = 10

final_pop = ea.evolve(generator=generate_agent,
                      evaluator=evaluate_agents,
                      pop_size=pop_size,
                      seeds = [[0.2, 0.82, 0.85, 5, 0, 0.7, 0.4, 0, 0.12, 0.25],
                               [0.2, 0.95, 0.9, 3, 0, 0.3, 0.4, 0.3, 0.08, 0.1],
                               [0.2, 1, 0.8, 3, 20, 0, 0, 0, 0.08, 0.1]],
                      maximize=True,
                      bounder=ec.Bounder([0, 0, 0, 1, 1, 0, 0, 0, 0, 0], 
                                        [1, 1, 1, 10, 20, 1, 1, 1, 1, 1]),
                      max_evaluations=evaluations,
                      max_time = 9000, # almost 3 days
                      num_crossover_points=2,
                      )

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
#end_main
