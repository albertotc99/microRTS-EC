#start_imports
from random import Random
from time import time
from datetime import datetime
import os
import csv
from inspyred import ec
from inspyred.ec import terminators
from inspyred.ec import evaluators
import subprocess
import pandas as pd
from io import StringIO
from multiprocessing import Pool
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


def meantime_to_win(df_games, id_ia):
    """
    Calcula el tiempo medio de victoria de un agente específico.
    
    Args:
        df_games: DataFrame con las partidas del torneo
        id_ia: ID del agente para el cual calcular el tiempo medio de victoria
        
    Returns:
        float: Tiempo medio de victoria (float('inf') si no hay victorias)
    """
    # Filtrar partidas donde el agente id_ia participa y gana
    # El agente puede estar como ai1 o ai2, y gana cuando winner coincide con su posición
    victories = df_games[
        ((df_games['ai1'] == id_ia) & (df_games['winner'] == 0)) |  # gana como ai1
        ((df_games['ai2'] == id_ia) & (df_games['winner'] == 1))    # gana como ai2
    ]
    
    if len(victories) == 0:
        return float('inf')  # No hay victorias
    
    # Calcular el tiempo medio de victoria
    mean_victory_time = victories['time'].mean()
    
    return mean_victory_time


def meantime_to_lose(df_games, id_ia):
    """
    Calcula el tiempo medio de derrota de un agente específico.
    
    Args:
        df_games: DataFrame con las partidas del torneo
        id_ia: ID del agente para el cual calcular el tiempo medio de derrota
        
    Returns:
        float: Tiempo medio de derrota (0 si no hay derrotas)
    """
    # Filtrar partidas donde el agente id_ia participa y pierde
    # El agente puede estar como ai1 o ai2, y pierde cuando winner NO coincide con su posición
    defeats = df_games[
        ((df_games['ai1'] == id_ia) & (df_games['winner'] == 1)) |  # pierde como ai1
        ((df_games['ai2'] == id_ia) & (df_games['winner'] == 0))    # pierde como ai2
    ]
    
    if len(defeats) == 0:
        return 0  # No hay derrotas
    
    # Calcular el tiempo medio de derrota
    mean_defeat_time = defeats['time'].mean()
    
    return mean_defeat_time


def count_total_wins(df_games, id_ia):
    """
    Calcula el número total de victorias de un agente específico.
    
    Args:
        df_games: DataFrame con las partidas del torneo
        id_ia: ID del agente para el cual calcular las victorias totales
        
    Returns:
        int: Número total de victorias
    """
    # Filtrar partidas donde el agente id_ia participa y gana
    # El agente puede estar como ai1 o ai2, y gana cuando winner coincide con su posición
    victories = df_games[
        ((df_games['ai1'] == id_ia) & (df_games['winner'] == 0)) |  # gana como ai1
        ((df_games['ai2'] == id_ia) & (df_games['winner'] == 1))    # gana como ai2
    ]
    
    return len(victories)


def count_total_ties(df_games, id_ia):
    """
    Calcula el número total de empates de un agente específico.
    
    Args:
        df_games: DataFrame con las partidas del torneo
        id_ia: ID del agente para el cual calcular los empates totales
        
    Returns:
        int: Número total de empates
    """
    # Filtrar partidas donde el agente id_ia participa y hay empate (winner = -1 o 2)
    # Nota: Verificar en MicroRTS cómo se codifican los empates
    ties = df_games[
        ((df_games['ai1'] == id_ia) | (df_games['ai2'] == id_ia)) & 
        (df_games['winner'] == -1)  # Asumiendo que -1 indica empate
    ]
    
    return len(ties)


def update_elo_ratings(elo_player1, elo_player2, result, k_factor=32):
    """
    Actualiza los ratings ELO de dos jugadores basándose en el resultado del enfrentamiento.
    
    Args:
        elo_player1 (float): Rating ELO actual del jugador 1
        elo_player2 (float): Rating ELO actual del jugador 2  
        result (float): Resultado del enfrentamiento desde la perspectiva del jugador 1:
                       1.0 = victoria del jugador 1
                       0.5 = empate
                       0.0 = victoria del jugador 2
        k_factor (int): Factor K que determina la sensibilidad del cambio (default: 32)
        
    Returns:
        tuple: (nuevo_elo_player1, nuevo_elo_player2)
    """
    # Calcular la probabilidad esperada de que el jugador 1 gane
    expected_score_player1 = 1 / (1 + 10**((elo_player2 - elo_player1) / 400))
    expected_score_player2 = 1 - expected_score_player1
    
    # Calcular los nuevos ratings
    new_elo_player1 = elo_player1 + k_factor * (result - expected_score_player1)
    new_elo_player2 = elo_player2 + k_factor * ((1 - result) - expected_score_player2)
    
    return new_elo_player1, new_elo_player2


def generate_agent(random, args):
    size = 10 # number of parameters

    agent = [random.random() for i in range(size)]
    agent[3] = random.randint(1,10) # number of workers
    agent[4] = random.randint(1,20) # attacking workers

    return agent


def play_match(args):
    """
    Ejecuta un enfrentamiento individual entre dos agentes.
    
    Args:
        args: tupla (i, j, agent_i, agent_j, class_path, folder_name)
        
    Returns:
        dict: resultado del enfrentamiento con victorias, empates y tiempos
    """
    i, j, agent_i, agent_j, class_path, folder_name = args
    
    # print(f"Ejecutando: AI {i} vs AI {j} -> {folder_name}")
    
    # Generar nombre único para el archivo usando solo timestamp y enfrentamiento
    timestamp = int(time() * 1000000)
    unique_filename = f"./resultados/{folder_name}/tournament_{i}vs{j}_{timestamp}.csv"
    
    # Preparar parámetros para el torneo 1vs1 (21 parámetros total)
    game_params = agent_i + agent_j + [unique_filename]  # 10 + 10 + 1 = 21 parámetros
    
    # Ejecutar CoEvEvaluationGame
    result_file = subprocess.run(['java', '-cp', class_path, 'tournament.CoEvEvaluationGame'] + 
                               [str(param) for param in game_params], 
                               capture_output=True, text=True)
    
    try:
        # Procesar resultado del torneo 1vs1 - leer desde archivo
        df = pd.read_csv(unique_filename)
        # Eliminar archivo temporal después de leerlo
        os.remove(unique_filename)
        
        games_df = load_tournament_games_from_df(df)
        
        # Contar victorias y empates para ambos agentes en este enfrentamiento
        wins_i = count_total_wins(games_df, 0)  # AI i juega como AI 0 en el torneo
        wins_j = count_total_wins(games_df, 1)  # AI j juega como AI 1 en el torneo
        ties_i = count_total_ties(games_df, 0)
        ties_j = count_total_ties(games_df, 1)
        
        # Calcular tiempos de victoria y derrota
        victory_time_i = meantime_to_win(games_df, 0)
        defeat_time_i = meantime_to_lose(games_df, 0)
        victory_time_j = meantime_to_win(games_df, 1)
        defeat_time_j = meantime_to_lose(games_df, 1)
        
        return {
            'i': i, 'j': j,
            'wins_i': wins_i, 'wins_j': wins_j,
            'ties_i': ties_i, 'ties_j': ties_j,
            'victory_time_i': victory_time_i, 'defeat_time_i': defeat_time_i,
            'victory_time_j': victory_time_j, 'defeat_time_j': defeat_time_j,
            'success': True
        }
    except Exception as e:
        # print(f"Error en enfrentamiento AI {i} vs AI {j}: {e}")
        return {
            'i': i, 'j': j,
            'wins_i': 0, 'wins_j': 0,
            'ties_i': 0, 'ties_j': 0,
            'victory_time_i': float('inf'), 'defeat_time_i': 0,
            'victory_time_j': float('inf'), 'defeat_time_j': 0,
            'success': False
        }


def evaluate_agents(candidates, args=None):
    fitness = []
    class_path = 'bin/' +\
      ':lib/hamcrest-all-1.3.jar:' +\
      'lib/jdom.jar:lib/junit-4.12.jar:' +\
      'lib/minimal-json-0.9.4.jar:lib/weka.jar:' +\
      'lib/MicroRTS.jar'
    
    # Obtener el nombre de la carpeta desde args
    folder_name = args.get('folder_name', 'CoEvGA') if args else 'CoEvGA'
    
    # Obtener número de procesos desde args
    mp_processes = args.get('mp_processes', 24) if args else 24
    
    # Obtener padres de la población actual
    parents = args['_ec'].population if args and '_ec' in args else []
    num_parents = len(parents)
    
    # Extraer candidatos de los padres
    parent_candidates = []
    for p in parents:
        parent_candidates.append(p.candidate)
    
    # Combinar padres y nuevos candidatos para el torneo
    all_candidates = parent_candidates + candidates
    nAIs = len(all_candidates)

    # Inicializar fitness acumulado para cada agente (padres + nuevos)
    accumulated_wins = [0] * nAIs
    accumulated_ties = [0] * nAIs
    victory_times = [[] for _ in range(nAIs)]
    defeat_times = [[] for _ in range(nAIs)]
    
    # Preparar lista de enfrentamientos
    matches = []
    for i in range(nAIs):
        for j in range(i + 1, nAIs):  # Solo desde i+1 para evitar duplicados
            matches.append((i, j, all_candidates[i], all_candidates[j], class_path, folder_name))
    
    # print(f"Ejecutando {len(matches)} enfrentamientos en paralelo...")
    
    # Paralelización de enfrentamientos
    with Pool(processes=mp_processes) as pool:
        results = pool.map(play_match, matches)
    
    # Procesar resultados de todos los enfrentamientos
    for result in results:
        if result['success']:
            i, j = result['i'], result['j']
            
            # Acumular victorias y empates
            accumulated_wins[i] += result['wins_i']
            accumulated_wins[j] += result['wins_j']
            accumulated_ties[i] += result['ties_i']
            accumulated_ties[j] += result['ties_j']
            
            # Acumular tiempos
            if result['victory_time_i'] != float('inf'):
                victory_times[i].append(result['victory_time_i'])
            if result['defeat_time_i'] != 0:
                defeat_times[i].append(result['defeat_time_i'])
            if result['victory_time_j'] != float('inf'):
                victory_times[j].append(result['victory_time_j'])
            if result['defeat_time_j'] != 0:
                defeat_times[j].append(result['defeat_time_j'])
            
            print(f"Completado: AI {i} vs AI {j} - Wins: {result['wins_i']}-{result['wins_j']}")
        else:
            #print(f"Enfrentamiento fallido: AI {result['i']} vs AI {result['j']}")
            pass
    
    # Calcular fitness final para cada agente y separar padres de nuevos candidatos
    all_fitness = []
    for id_ia in range(nAIs):
        total_wins = accumulated_wins[id_ia]
        total_ties = accumulated_ties[id_ia]
        ind_fitness = total_wins + (total_ties * 0.5)
        
        # Calcular tiempos medios
        avg_victory_time = sum(victory_times[id_ia]) / len(victory_times[id_ia]) if victory_times[id_ia] else float('inf')
        avg_defeat_time = sum(defeat_times[id_ia]) / len(defeat_times[id_ia]) if defeat_times[id_ia] else 0
        
        lexical_fitness = LexicoFitness(ind_fitness, avg_victory_time, avg_defeat_time)
        all_fitness.append(lexical_fitness)
        
        print(f"AI {id_ia} FINAL: {total_wins} victorias, {total_ties} empates, fitness={ind_fitness}")
    
    # Actualizar fitness de los padres y retornar fitness de nuevos candidatos
    fitness = []
    for i, calculated_fitness in enumerate(all_fitness):
        if i < num_parents:
            # Actualizar fitness del padre
            args['_ec'].population[i].fitness = calculated_fitness
            #print(f"Actualizado fitness del padre {i}: {calculated_fitness}")
        else:
            # Añadir fitness del nuevo candidato
            fitness.append(calculated_fitness)
            # print(f"Fitness del nuevo candidato {i-num_parents}: {calculated_fitness}")
    
    return fitness



def evaluate_agents_elo(candidates, args=None):
    class_path = 'bin/' +\
      ':lib/hamcrest-all-1.3.jar:' +\
      'lib/jdom.jar:lib/junit-4.12.jar:' +\
      'lib/minimal-json-0.9.4.jar:lib/weka.jar:' +\
      'lib/MicroRTS.jar'
    
    # Obtener el nombre de la carpeta desde args
    folder_name = args.get('folder_name', 'CoEvELO') if args else 'CoEvELO'
    
    # Obtener número de procesos desde args
    mp_processes = args.get('mp_processes', 32) if args else 32
    
    # Obtener padres de la población actual
    parents = args['_ec'].population if args and '_ec' in args else []
    num_parents = len(parents)
    
    # Extraer candidatos de los padres
    parent_candidates = []
    for p in parents:
        parent_candidates.append(p.candidate)
    
    # Combinar padres y nuevos candidatos para el torneo
    all_candidates = parent_candidates + candidates
    nAIs = len(all_candidates)
    
    # Inicializar ratings ELO: padres con su fitness actual, nuevos con 1200
    elo_ratings = []
    for i in range(nAIs):
        if i < num_parents:
            # Padres mantienen su ELO actual (fitness)
            current_elo = parents[i].fitness if hasattr(parents[i], 'fitness') and parents[i].fitness is not None else 1200.0
            elo_ratings.append(current_elo)
        else:
            # Nuevos candidatos empiezan con 1200
            elo_ratings.append(1200.0)
    
    # Generar TODOS los emparejamientos de TODAS las rondas de una vez
    all_rounds = generate_all_round_pairings(nAIs)
    num_rounds = len(all_rounds)
    
    # Obtener todos los enfrentamientos únicos
    all_unique_matches = set()
    for round_matches in all_rounds:
        all_unique_matches.update(round_matches)
    
    total_matches = len(all_unique_matches)
    # print(f"Iniciando torneo ELO de {num_rounds} rondas con {nAIs} agentes...")
    # print(f"Ejecutando TODOS los {total_matches} enfrentamientos únicos en paralelo...")
    
    # ===== FASE 1: EJECUTAR TODOS LOS ENFRENTAMIENTOS =====
    all_matches = []
    for i, j in all_unique_matches:
        all_matches.append((i, j, all_candidates[i], all_candidates[j], class_path, folder_name))
    
    # Ejecutar TODOS los enfrentamientos en paralelo de una sola vez
    with Pool(processes=mp_processes) as pool:
        all_results = pool.map(play_match, all_matches)
    
    # Crear matriz de resultados para acceso rápido
    results_matrix = {}
    for result in all_results:
        i, j = result['i'], result['j']
        key = (min(i, j), max(i, j))  # Normalizar clave
        results_matrix[key] = result
    
    # print(f"Completados todos los enfrentamientos. Simulando torneo por rondas...")
    
    # ===== FASE 2: SIMULAR TORNEO RONDA POR RONDA =====
    for round_num, round_matches in enumerate(all_rounds):
        print(f"\n--- RONDA {round_num + 1}/{num_rounds} ---")
        print(f"Procesando {len(round_matches)} enfrentamientos de la ronda {round_num + 1}...")
        
        # Procesar resultados de esta ronda y actualizar ELO
        for i, j in round_matches:
            key = (min(i, j), max(i, j))
            result = results_matrix[key]
            
            if result['success']:
                total_wins_i = result['wins_i']
                total_wins_j = result['wins_j']
                total_ties_i = result['ties_i']
                
                total_games = total_wins_i + total_wins_j + total_ties_i
                
                if total_games > 0:
                    # Calcular el score del jugador i
                    score_i = (total_wins_i + 0.5 * total_ties_i) / total_games
                    
                    # Guardar ELO actual para mostrar el cambio
                    old_elo_i, old_elo_j = elo_ratings[i], elo_ratings[j]
                    
                    # Actualizar ratings ELO
                    new_elo_i, new_elo_j = update_elo_ratings(
                        elo_ratings[i], 
                        elo_ratings[j], 
                        score_i,
                        k_factor=32
                    )
                    
                    elo_ratings[i] = new_elo_i
                    elo_ratings[j] = new_elo_j
                    
                    print(f"  AI {i} vs AI {j} - Score: {score_i:.2f} - ELO: {old_elo_i:.1f}→{new_elo_i:.1f} vs {old_elo_j:.1f}→{new_elo_j:.1f}")
            else:
                print(f"  Enfrentamiento fallido: AI {i} vs AI {j}")
        
        # Mostrar ranking actual después de cada ronda
        ranking = sorted(enumerate(elo_ratings), key=lambda x: x[1], reverse=True)
        #print(f"Ranking después de ronda {round_num + 1}:")
        #for pos, (agent_id, elo) in enumerate(ranking[:5], 1):  # Top 5
            #print(f"  {pos}. AI {agent_id}: {elo:.1f}")
    
    print(f"\n--- TORNEO FINALIZADO ---")
    final_ranking = sorted(enumerate(elo_ratings), key=lambda x: x[1], reverse=True)
    print("Ranking final:")
    for pos, (agent_id, elo) in enumerate(final_ranking, 1):
        print(f"  {pos}. AI {agent_id}: {elo:.1f}")
    
    # Actualizar fitness de los padres y retornar fitness de nuevos candidatos
    fitness = []
    for i, elo_rating in enumerate(elo_ratings):
        if i < num_parents:
            # Actualizar fitness del padre
            args['_ec'].population[i].fitness = elo_rating
            #print(f"Actualizado fitness del padre {i}: {elo_rating:.1f}")
        else:
            # Añadir fitness del nuevo candidato
            fitness.append(elo_rating)
            #print(f"Fitness del nuevo candidato {i-num_parents}: {elo_rating:.1f}")

    print(f"\n\n")
    return fitness


def generate_all_round_pairings(num_agents):
    """
    Genera todos los emparejamientos para todas las rondas de un torneo round-robin.
    Cada agente juega exactamente una vez por ronda.
    
    Args:
        num_agents (int): Número total de agentes
        
    Returns:
        list: Lista de rondas, donde cada ronda es una lista de tuplas (i, j)
    """
    if num_agents < 2:
        return []
    
    # Si el número es impar, añadir un "dummy" player
    players = list(range(num_agents))
    if num_agents % 2 == 1:
        players.append(-1)  # -1 representa "descanso"
    
    n = len(players)
    rounds = []
    
    # Algoritmo clásico de round-robin
    # El jugador 0 se mantiene fijo, los demás rotan
    for round_num in range(n - 1):
        round_matches = []
        
        # Emparejar jugadores
        for i in range(n // 2):
            player1 = players[i]
            player2 = players[n - 1 - i]
            
            # Solo añadir si ninguno es el "dummy" player
            if player1 != -1 and player2 != -1:
                # Asegurar orden consistente
                pair = (min(player1, player2), max(player1, player2))
                round_matches.append(pair)
        
        rounds.append(round_matches)
        
        # Rotar jugadores (excepto el primero que se mantiene fijo)
        players = [players[0]] + [players[-1]] + players[1:-1]
    
    return rounds


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

def run_coev_experiment(use_elo_evaluation=True, generations=50, pop_size=10, mp_processes=32):
    # Generar y guardar la seed para replicabilidad
    seed_value = int(time())
    rand = Random()
    rand.seed(seed_value)
    ea = ec.GA(rand)
    ea.selector = ec.selectors.rank_selection
    ea.terminator = [terminators.evaluation_termination, terminators.time_termination]
    ea.observer = ec.observers.file_observer
    ea.replacer = ec.replacers.plus_replacement 
    ea.variator = [ec.variators.uniform_crossover, my_uniform_mutation_variator]

    # Configuración del experimento
    evaluation_type = "ELO" if use_elo_evaluation else "GA"
    evaluator_function = evaluate_agents_elo if use_elo_evaluation else evaluate_agents

    # Crear carpeta única para esta ejecución
    timestamp = datetime.now().strftime("%m%d%Y-%H%M%S")
    folder_name = f"CoEv{evaluation_type}_{timestamp}"
    results_folder = f"./resultados/{folder_name}"
    os.makedirs(results_folder, exist_ok=True)

    evaluations = pop_size * generations

    inicio = time()
    final_pop = ea.evolve(generator=generate_agent,
                          evaluator=evaluator_function,
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
                          folder_name=folder_name,
                          mp_processes=mp_processes)
    fin = time()

    final_pop.sort(reverse=True)

    # Guardar estadísticas incluyendo la seed y configuración
    stats_file = f"{results_folder}/CoEvstats_{evaluation_type.lower()}-{timestamp}.txt"
    with open(stats_file, 'w') as file:
        file.write(f"Seed: {seed_value}\n")
        file.write(f"{fin-inicio} seconds employed\n")
        file.write(f"{evaluations} evaluations\n")
        file.write(f"{generations} generations\n")
        file.write(f"{pop_size} pop size\n")
        file.write(f"{mp_processes} mp_processes\n")
        file.write(f"Evaluation type: {evaluation_type}\n")
        file.write("Best individual\n")
        file.write(f"{str(final_pop[0])}\n")

    pd.DataFrame(final_pop).to_csv(f"{results_folder}/CoEvpopulation-{evaluation_type.lower()}-{timestamp}.csv")
    
    return final_pop[0], fin-inicio, evaluation_type, results_folder

if __name__ == "__main__":
    # Configuración de experimentos
    NUM_EXPERIMENTS = 1
    USE_ELO = False
    GENERATIONS = 1
    POP_SIZE = 15
    MP_PROCESSES = 12

    for i in range(NUM_EXPERIMENTS):
        print(f"Experimento CoEv {i+1}/{NUM_EXPERIMENTS}")
        best_individual, tiempo, eval_type, folder = run_coev_experiment(
            use_elo_evaluation=USE_ELO,
            generations=GENERATIONS,
            pop_size=POP_SIZE,
            mp_processes=MP_PROCESSES
        )
        print(f"Mejor: {str(best_individual)}, Tiempo: {tiempo:.2f}s, Tipo: {eval_type}")
        print(f"Guardado en: {folder}\n")
