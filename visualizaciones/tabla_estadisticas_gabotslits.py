#!/usr/bin/env python3
"""
Script para generar una tabla con estadísticas de las optimizaciones GABotsLit
Por cada run muestra:
- Media del fitness del mejor individuo
- Desviación típica del fitness del mejor individuo
- Tiempo de ejecución
- Fitness medio de la población final
- Número de procesadores utilizados
"""

import os
import re
import glob
import pandas as pd
import numpy as np
from pathlib import Path

def parse_stats_file(filepath):
    """
    Extrae información del archivo stats_ga_*.txt
    Retorna: (seed, tiempo_segundos, evaluaciones, pop_size, mp_nprocs, mejor_individuo_fitness)
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    seed_match = re.search(r'Seed:\s*(\d+)', content)
    time_match = re.search(r'([\d.]+)\s+seconds employed', content)
    evals_match = re.search(r'(\d+)\s+evaluations', content)
    pop_match = re.search(r'(\d+)\s+pop size', content)
    procs_match = re.search(r'(\d+)\s+mp_nprocs', content)
    
    # El mejor individuo tiene formato: [...] : (fitness1, fitness2, fitness3)
    best_match = re.search(r'\]\s*:\s*\(([\d.]+),\s*([\d.]+),\s*([\d.]+)\)', content)
    
    seed = int(seed_match.group(1)) if seed_match else None
    tiempo = float(time_match.group(1)) if time_match else None
    evals = int(evals_match.group(1)) if evals_match else None
    pop_size = int(pop_match.group(1)) if pop_match else None
    mp_nprocs = int(procs_match.group(1)) if procs_match else None
    
    if best_match:
        # El fitness parece ser una tupla, usaremos el primer valor
        fitness_mejor = float(best_match.group(1))
    else:
        fitness_mejor = None
    
    return seed, tiempo, evals, pop_size, mp_nprocs, fitness_mejor

def parse_statistics_csv(filepath):
    """
    Extrae información del archivo inspyred-statistics-file-*.csv
    Retorna: media y std de los mejores fitness de todas las generaciones
    """
    try:
        # Leer el archivo línea por línea para evitar problemas con las tuplas
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        if len(lines) == 0:
            return None, None
        
        # Extraer el mejor fitness de cada generación
        best_fitness_per_gen = []
        
        for line in lines:
            line = line.strip()
            # Formato: gen, popsize, worst(tuple), best(tuple), median, mean, std
            # Buscar el patrón de la tupla best (después del worst)
            best_match = re.search(r'\),\s*\(([\d.]+),', line)
            if best_match:
                best_fitness_per_gen.append(float(best_match.group(1)))
        
        if best_fitness_per_gen:
            mean_best = np.mean(best_fitness_per_gen)
            std_best = np.std(best_fitness_per_gen)
            return mean_best, std_best
        else:
            return None, None
        
    except Exception as e:
        print(f"Error parseando {filepath}: {e}")
        return None, None

def parse_final_population(filepath):
    """
    Calcula estadísticas de la población final
    Retorna: (mejor_fitness, media_fitness, std_fitness)
    """
    try:
        # El archivo tiene formato CSV con el fitness al final
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        fitness_values = []
        for line in lines:
            # Buscar el patrón de fitness: (val1, val2, val3)
            match = re.search(r'\((\d+\.?\d*),\s*(\d+\.?\d*),\s*(\d+\.?\d*)\)', line)
            if match:
                # Usar el primer valor del fitness
                fitness_values.append(float(match.group(1)))
        
        if fitness_values:
            return max(fitness_values), np.mean(fitness_values), np.std(fitness_values)
        else:
            return None, None, None
            
    except Exception as e:
        print(f"Error parseando población final {filepath}: {e}")
        return None, None, None

def analyze_gabotslit_runs():
    """
    Analiza todas las carpetas GABotsLit_* y genera estadísticas
    """
    base_dir = Path('/home/albertotc99/Documentos/TFG/myAgentMicroRTS/resultados')
    
    # Buscar todas las carpetas GABotsLit_*
    gabotslit_dirs = sorted(glob.glob(str(base_dir / 'GABotsLit_*')))
    
    print(f"Encontradas {len(gabotslit_dirs)} carpetas GABotsLit_*\n")
    
    results = []
    
    for i, dir_path in enumerate(gabotslit_dirs, 1):
        dir_name = os.path.basename(dir_path)
        print(f"Procesando {dir_name}...")
        
        # Buscar archivos relevantes
        stats_file = glob.glob(os.path.join(dir_path, 'stats_ga_*.txt'))
        csv_stats_file = glob.glob(os.path.join(dir_path, 'inspyred-statistics-file-*.csv'))
        final_pop_file = glob.glob(os.path.join(dir_path, 'Final_population_*.csv'))
        
        if not stats_file:
            print(f"  ⚠️  No se encontró archivo stats_ga en {dir_name}")
            continue
        
        # Parsear stats_ga
        seed, tiempo, evals, pop_size, mp_nprocs, fitness_mejor_stats = parse_stats_file(stats_file[0])
        
        # Parsear statistics CSV si existe (media y std de mejores individuos por generación)
        mean_best_gen, std_best_gen = None, None
        if csv_stats_file:
            mean_best_gen, std_best_gen = parse_statistics_csv(csv_stats_file[0])
        
        # Parsear población final si existe
        best_final_pop, mean_final_pop, std_final_pop = None, None, None
        if final_pop_file:
            best_final_pop, mean_final_pop, std_final_pop = parse_final_population(final_pop_file[0])
        
        # Usar el mejor fitness disponible
        best_fitness = fitness_mejor_stats if fitness_mejor_stats is not None else best_final_pop
        
        results.append({
            'Run': i,
            'Carpeta': dir_name,
            'Seed': seed,
            'Tiempo (seg)': tiempo,
            'Tiempo (horas)': tiempo / 3600 if tiempo else None,
            'Evaluaciones': evals,
            'Tamaño Población': pop_size,
            'Procesadores': mp_nprocs,
            'Mejor Fitness': best_fitness,
            'Media Mejor Fitness x Gen': mean_best_gen,
            'Std Mejor Fitness x Gen': std_best_gen,
            'Media Fitness Pob. Final': mean_final_pop,
            'Std Fitness Pob. Final': std_final_pop
        })
    
    # Crear DataFrame
    df = pd.DataFrame(results)
    
    # Calcular estadísticas globales
    print("\n" + "="*80)
    print("TABLA DE RESULTADOS POR RUN - GABotsLit")
    print("="*80 + "\n")
    
    # Tabla principal
    display_df = df[['Run', 'Carpeta', 'Mejor Fitness', 'Media Mejor Fitness x Gen', 
                     'Std Mejor Fitness x Gen', 'Media Fitness Pob. Final', 
                     'Std Fitness Pob. Final', 'Tiempo (horas)', 'Procesadores']].copy()
    
    print(display_df.to_string(index=False))
    
    # Resumen estadístico
    print("\n" + "="*80)
    print("RESUMEN ESTADÍSTICO (10 RUNS) - GABotsLit")
    print("="*80 + "\n")
    
    summary_data = {
        'Métrica': [
            'Media del Mejor Fitness Final',
            'Desv. Típica del Mejor Fitness Final',
            'Media del Mejor Fitness x Gen (promedio)',
            'Desv. Típica del Mejor Fitness x Gen (promedio)',
            'Media Fitness Pob. Final (promedio)',
            'Desv. Típica Fitness Pob. Final (promedio)',
            'Tiempo Ejecución Medio (horas)',
            'Desv. Típica Tiempo (horas)',
            'Procesadores (común a todas)'
        ],
        'Valor': [
            df['Mejor Fitness'].mean(),
            df['Mejor Fitness'].std(),
            df['Media Mejor Fitness x Gen'].mean(),
            df['Std Mejor Fitness x Gen'].mean(),
            df['Media Fitness Pob. Final'].mean(),
            df['Std Fitness Pob. Final'].mean(),
            df['Tiempo (horas)'].mean(),
            df['Tiempo (horas)'].std(),
            df['Procesadores'].iloc[0] if len(df) > 0 else None
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))
    
    # Guardar resultados
    output_file = base_dir / 'Tabla_Estadisticas_GABotsLit.csv'
    df.to_csv(output_file, index=False)
    print(f"\n✓ Resultados guardados en: {output_file}")
    
    # Guardar también en formato más legible
    output_txt = base_dir / 'Tabla_Estadisticas_GABotsLit.txt'
    with open(output_txt, 'w') as f:
        f.write("="*80 + "\n")
        f.write("TABLA DE RESULTADOS POR RUN - GABotsLit\n")
        f.write("="*80 + "\n\n")
        f.write(display_df.to_string(index=False))
        f.write("\n\n" + "="*80 + "\n")
        f.write("RESUMEN ESTADÍSTICO (10 RUNS) - GABotsLit\n")
        f.write("="*80 + "\n\n")
        f.write(summary_df.to_string(index=False))
        f.write("\n")
    
    print(f"✓ Resumen guardado en: {output_txt}")
    
    return df

if __name__ == '__main__':
    df = analyze_gabotslit_runs()
