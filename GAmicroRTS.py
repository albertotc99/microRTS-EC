#start_imports
from random import Random
from time import time
from datetime import datetime
from inspyred import ec
from inspyred.ec import terminators
from inspyred.ec import evaluators
import subprocess
import pandas as pd
from io import StringIO
import os
#end_imports

class LexicoFitness(float):
    def __new__(cls, victorias, tiempo_victoria, tiempo_derrota):
        # El valor float será solo las victorias para numpy
        obj = float.__new__(cls, victorias)
        obj.victorias = victorias
        obj.tiempo_victoria = tiempo_victoria
        obj.tiempo_derrota = tiempo_derrota
        return obj

    def __lt__(self, other):
        if isinstance(other, LexicoFitness):
            if self.victorias != other.victorias:
                return self.victorias < other.victorias
            elif self.tiempo_victoria != other.tiempo_victoria:
                return self.tiempo_victoria > other.tiempo_victoria  # menor es mejor
            else:
                return self.tiempo_derrota < other.tiempo_derrota  # mayor es mejor
        return float(self) < float(other)

    def __eq__(self, other):
        if isinstance(other, LexicoFitness):
            return (self.victorias == other.victorias and
                    self.tiempo_victoria == other.tiempo_victoria and
                    self.tiempo_derrota == other.tiempo_derrota)
        return float(self) == float(other)
    
    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)
    
    def __gt__(self, other):
        return not self.__le__(other)
    
    def __ge__(self, other):
        return not self.__lt__(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)

    # Métodos para pickle (necesario para multiprocessing)
    def __getnewargs__(self):
        """Devuelve los argumentos necesarios para __new__ durante unpickling."""
        return (self.victorias, self.tiempo_victoria, self.tiempo_derrota)

    def __repr__(self):
        return f"({self.victorias}, {self.tiempo_victoria}, {self.tiempo_derrota})"

def load_tournament_games_from_df(df):
    """
    Extrae los datos de partidas desde un DataFrame de torneo.
    
    Args:
        df (pd.DataFrame): DataFrame completo del torneo
        
    Returns:
        pd.DataFrame: DataFrame con solo los datos de las partidas
        
    Raises:
        ValueError: Si no se encuentra la estructura esperada del DataFrame
    """
    # Convertir DataFrame a líneas de texto para procesar
    lines = []
    for index, row in df.iterrows():
        # Convertir la fila a string, manejando valores NaN
        row_str = '\t'.join(str(val) if pd.notna(val) else '' for val in row.values)
        lines.append(row_str + '\n')
    
    # Buscar la línea de headers y el inicio de estadísticas
    header_line_idx = None
    stats_start_idx = None
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # Buscar headers de columnas
        if header_line_idx is None and all(col in line for col in ['iteration', 'map', 'ai1', 'ai2']):
            header_line_idx = i
        
        # Buscar inicio de estadísticas
        elif stripped_line == "Wins:":
            stats_start_idx = i
            break
    
    if header_line_idx is None:
        raise ValueError("No se encontró la línea de headers en el DataFrame")
    
    # Extraer líneas de datos de partidas
    end_idx = stats_start_idx if stats_start_idx else len(lines)
    data_lines = lines[header_line_idx:end_idx]
    
    # Crear DataFrame optimizado
    csv_content = ''.join(data_lines)
    return pd.read_csv(StringIO(csv_content), sep='\t')


def generate_agent(random, args):
    size = 10 # number of parameters

    agent = [random.random() for i in range(size)]
    agent[3] = random.randint(1,10) # number of workers
    agent[4] = random.randint(1,20) # attacking workers

    return agent


def meantime_to_win(df_games):
    """
    Calcula el tiempo medio de victoria de un agente (ai1=0).
    
    Args:
        df_games: DataFrame con las partidas del torneo
        
    Returns:
        float: Tiempo medio de victoria (0 si no hay victorias)
    """
    # Filtrar solo las partidas donde ai1=0 (nuestro agente) y winner=0 (ganó nuestro agente)
    victories = df_games[(df_games['ai1'] == 0) & (df_games['winner'] == 0)]
    
    if len(victories) == 0:
        return float('inf')  # No hay victorias
    
    # Calcular el tiempo medio de victoria
    mean_victory_time = victories['time'].mean()
    
    return mean_victory_time

def meantime_to_lose(df_games):
    """
    Calcula el tiempo medio de derrota de un agente (ai1=0).
    
    Args:
        df_games: DataFrame con las partidas del torneo
        
    Returns:
        float: Tiempo medio de derrota (0 si no hay derrotas)
    """
    # Filtrar solo las partidas donde ai1=0 (nuestro agente) y winner=1 (ganó el oponente)
    defeats = df_games[(df_games['ai1'] == 0) & (df_games['winner'] == 1)]
    
    if len(defeats) == 0:
        return 0  # No hay derrotas
    
    # Calcular el tiempo medio de derrota
    mean_defeat_time = defeats['time'].mean()
    
    return mean_defeat_time

def evaluate_agent(candidate=None, args=None):
    fitness = []
    class_path = 'bin/' +\
      ':lib/hamcrest-all-1.3.jar:' +\
      'lib/jdom.jar:lib/junit-4.12.jar:' +\
      'lib/minimal-json-0.9.4.jar:lib/weka.jar:' +\
      'lib/MicroRTS.jar'

    # Obtener el nombre de la carpeta desde args
    folder_name = args.get('folder_name', 'GABotsLit')  # valor por defecto
    
    # Generar nombre único para el archivo basado en process ID y timestamp
    process_id = os.getpid()
    timestamp = int(time() * 1000000)  # microsegundos para mayor unicidad
    filename = f"./resultados/{folder_name}/tournament_{process_id}_{timestamp}.csv"
    
    result_file = subprocess.run(['java', '-cp', class_path, 'tournament.EvaluationTournament'] + 
                                 [str(c) for c in candidate[0]] + [filename], capture_output=True, text=True)

    # Read CSV file from the generated file
    try:
        df = pd.read_csv(filename)
        # Eliminar el archivo temporal después de leerlo
        os.remove(filename)
    except FileNotFoundError:
        # Si no se pudo crear el archivo, devolver fitness 0
        return [LexicoFitness(0, float('inf'), 0)]
    
    offset = 14
    nAIs = 1
    nOpponentAIs = 3
    nMaps = 5
    nIter = 4
    wins_row_idx = (offset + nMaps + nAIs + nOpponentAIs + (nOpponentAIs * nMaps * nIter)) - 2 # Minus 2 because of the column label and 0 indexing
    ties_row_idx = wins_row_idx + 2

    # check number of rows
    if len(df) >= ties_row_idx:
        wins_row = df.iloc[wins_row_idx]
        ties_row = df.iloc[ties_row_idx]

        # convert to numeric and sum the values 
        if (nOpponentAIs > 1):
            ind_fitness = sum(float(wins) for wins in wins_row.iloc[0].split('\t') if wins)
            ind_fitness += sum(float(ties) for ties in ties_row.iloc[0].split('\t') if ties) * 0.5
            # Calcular tiempos medios usando las partidas individuales
            games_df = load_tournament_games_from_df(df)
            ind_victory_time = meantime_to_win(games_df)
            ind_defeat_time = meantime_to_lose(games_df)
        else:
            ind_fitness = int(wins_row) + 0.5*int(ties_row)
            # Calcular tiempos medios usando las partidas individuales
            games_df = load_tournament_games_from_df(df)
            ind_victory_time = meantime_to_win(games_df)
            ind_defeat_time = meantime_to_lose(games_df)

        fitness.append(LexicoFitness(ind_fitness, ind_victory_time, ind_defeat_time))
    else:
        fitness.append(LexicoFitness(0, float('inf'), 0))

    return fitness

def my_uniform_mutation_variator(random, candidates, args):
    mutation_rate = args.get('mutation_rate', 0.15)
    mutants = []
    
    for c in candidates:
        mutant = list(c)  # copia para no modificar el original
        for i in range(len(mutant)):
            if random.random() < mutation_rate:
                # muta según el tipo o rango del gen
                if i == 3:
                    mutant[i] = random.randint(1, 10)
                elif i == 4:
                    mutant[i] = random.randint(1, 20)
                else:
                    mutant[i] = random.random()

        mutants.append(mutant)
    return mutants

def run_experiment(mp_nprocs=15, evaluations=2, pop_size=2):
    # Generar y guardar la seed para replicabilidad
    seed_value = int(time())
    rand = Random()
    rand.seed(seed_value)
    ea = ec.GA(rand)
    ea.selector = ec.selectors.tournament_selection
    ea.terminator = [terminators.evaluation_termination, terminators.time_termination]
    ea.observer = ec.observers.file_observer
    ea.variator = [ec.variators.uniform_crossover, my_uniform_mutation_variator]
    ea.replacer = ec.replacers.plus_replacement

    timestamp = datetime.now().strftime("%m%d%Y-%H%M%S")
    folder_name = f"GABotsLit_{timestamp}"
    results_folder = f"./resultados/{folder_name}"
    os.makedirs(results_folder, exist_ok=True)

    inicio = time()
    final_pop = ea.evolve(generator=generate_agent,
                          evaluator=evaluators.parallel_evaluation_mp,
                          pop_size=pop_size,
                        seeds = [
                              # agentes GABotsLit
                              [0.8236764429411386, 0.3421385248489114, 0.03804993858450434, 5, 12, 0.6771749205448041, 0.10525102343194481, 0.9302053416800453, 0.4498789212944384, 0.44761875467539647, "GABotsLit"],
                              [0.12297458178514886, 0.6892306869658429, 0.7148493268065897, 6, 14, 0.8592884890421564, 0.5742506862351809, 0.5004585268846088, 0.4516465027404083, 0.016439674148995054, "GABotsLit"],
                              [0.2852493952791957, 0.030117081355244824, 0.5725553409674055, 6, 17, 0.2861725587415407, 0.9271914077457131, 0.2664893851232498, 0.5158698667832745, 0.30820488364743004, "GABotsLit"],
                              [0.24828854117733912, 0.8999707242482075, 0.7263712750326307, 1, 19, 0.8089887021281921, 0.44300790338559803, 0.5108326262050714, 0.226295668792857, 0.9835853623793082, "GABotsLit"],
                              [0.965954342890369, 0.4145858805797874, 0.5024027405763758, 8, 17, 0.6860722488962545, 0.9487061328399283, 0.03804765977886704, 0.11268153953011151, 0.20435247897995978, "GABotsLit"],
                              # agentes CoEvELO
                              [0.16846696454019505, 0.9633468064642499, 0.789097289541181, 2, 19, 0.8795128759915216, 0.9204724802858336, 0.3887979788155116, 0.8242883235207035, 0.6129754483818649, "CoEvELO"],
                              [0.956636271863732, 0.2579380498672741, 0.6393568712921733, 7, 17, 0.023178269925433037, 0.1866656204511874, 0.8990435733515699, 0.6637621419651777, 0.7502877068361935, "CoEvELO"],
                              [0.8466639164968095, 0.2786706656361061, 0.030620401970831934, 7, 18, 0.0600575737756297, 0.8293527663885787, 0.5109352989009032, 0.7824192308453812, 0.5438145140559759, "CoEvELO"],
                              [0.9291443488886724, 0.7502030751695131, 0.7437527057678102, 2, 2, 0.511100935792232, 0.7213028361032197, 0.5590256083711386, 0.2615184431104183, 0.7774327843360552, "CoEvELO"],
                              [0.10373467819859672, 0.961272247785899, 0.8833467825088809, 6, 7, 0.3245942883610985, 0.9685604724645657, 0.6039455496315845, 0.13132116016646456, 0.6308930758328315, "CoEvELO"],
                              # coev GA
                              [0.5296680302038603, 0.7913396501236944, 0.1484756029295331, 6, 1, 0.6141293126585077, 0.7893003170753544, 0.27548353980645435, 0.1367370822796239, 0.32084294928487345, "CoEvGA"],
                              [0.4859717980626773, 0.6061377722530442, 0.7690359014217759, 5, 2, 0.5359423083410759, 0.2502058625939866, 0.21263002112864848, 0.9258892735541014, 0.8120464407808758, "CoEvGA"],
                              [0.9609987620355505, 0.20610609964580984, 0.507066433589285, 4, 4, 0.9707413947048525, 0.3705438550855966, 0.19917051121690899, 0.18188515852994291, 0.1173103447579249, "CoEvGA"],
                              [0.18243372802157765, 0.018896528679374525, 0.8960905257877619, 5, 11, 0.9502573366218408, 0.608636223992721, 0.3560660179061693, 0.3398173646106416, 0.2635904919086409, "CoEvGA"],
                              [0.3390729325360927, 0.1305158934195393, 0.06912474831286741, 8, 2, 0.7841551494600603, 0.8182534032606329, 0.7844896246021426, 0.4211679057584541, 0.7454018349476341, "CoEvGA"]
                                 ],
                          maximize=True,
                          bounder=ec.Bounder([0, 0, 0, 1, 1, 0, 0, 0, 0, 0], 
                                            [1, 1, 1, 10, 20, 1, 1, 1, 1, 1]),
                          max_evaluations=evaluations,
                          max_time = 300000,
                          mp_evaluator=evaluate_agent,
                          mp_nprocs=mp_nprocs,
                          folder_name=folder_name)
    fin = time()

    final_pop.sort(reverse=True)

    stats_file = f"{results_folder}/stats_ga_{timestamp}.txt"
    with open(stats_file, 'w') as file:
        file.write(f"Seed: {seed_value}\n")
        file.write(f"{fin-inicio} seconds employed\n")
        file.write(f"{evaluations} evaluations\n")
        file.write(f"{pop_size} pop size\n")
        file.write(f"{mp_nprocs} mp_nprocs\n")
        file.write("Best individual\n")
        file.write(f"{str(final_pop[0])}\n")

    pd.DataFrame(final_pop).to_csv(f"{results_folder}/Final_population_{timestamp}.csv")
    
    return final_pop[0], fin-inicio

if __name__ == "__main__":
    NUM_EXPERIMENTS = 1
    MP_NPROCS = 10
    EVALUATIONS = 15
    POP_SIZE = 15

    for i in range(NUM_EXPERIMENTS):
        print(f"Experimento {i+1}/{NUM_EXPERIMENTS}")
        best_individual, tiempo = run_experiment(mp_nprocs=MP_NPROCS, evaluations=EVALUATIONS, pop_size=POP_SIZE)
        print(f"Mejor: {str(best_individual)}, Tiempo: {tiempo:.2f}s\n")