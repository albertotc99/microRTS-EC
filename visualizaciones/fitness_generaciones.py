#!/usr/bin/env python3
"""
Visualización de la evolución del fitness según el número de generación.
Muestra en una misma gráfica: min, max, mediana, media y desviación típica.

El fitness se calcula como: número de victorias + 0.5 * número de empates
Los tiempos medios (para ganar/perder) se ignoran en esta visualización.
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import sys
from pathlib import Path
from datetime import datetime

# Configuración de estilo
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# CONFIGURACIÓN DE NOMBRES DE ARCHIVOS
# Cambiar solo estas variables para modificar el comportamiento de nombrado
FILE_SUFFIX = "CoEvELO1"  # Sufijo personalizado (ej: "GABotsLit", "Experimento1", etc.)
USE_TIMESTAMP = True       # Si True, agrega timestamp para evitar sobreescrituras
                          # Si False, solo usa el sufijo personalizado

def generate_timestamp_suffix():
    """
    Genera un sufijo con timestamp para evitar sobreescribir archivos.
    Formato: YYYYMMDD-HHMMSS
    """
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def create_filename(base_name, output_dir='imagenes', suffix=None, use_timestamp=None):
    """
    Crea un nombre de archivo completo con sufijo parametrizado.
    
    Args:
        base_name: Nombre base del archivo (sin extensión)
        output_dir: Directorio de salida
        suffix: Sufijo personalizado (si None, usa FILE_SUFFIX global)
        use_timestamp: Si usar timestamp (si None, usa USE_TIMESTAMP global)
    
    Returns:
        Ruta completa del archivo
        
    Ejemplos de nombres generados:
        - Con FILE_SUFFIX="GABotsLit" y USE_TIMESTAMP=True:
          "fitness_evolution_complete-GABotsLit-20241024-143052.png"
        - Con FILE_SUFFIX="Test" y USE_TIMESTAMP=False:
          "fitness_evolution_complete-Test.png"
        - Con FILE_SUFFIX="" y USE_TIMESTAMP=True:
          "fitness_evolution_complete-20241024-143052.png"
    """
    # Usar parámetros globales si no se especifican
    file_suffix = suffix if suffix is not None else FILE_SUFFIX
    use_ts = use_timestamp if use_timestamp is not None else USE_TIMESTAMP
    
    # Construir el sufijo completo
    parts = []
    if file_suffix:
        parts.append(file_suffix)
    if use_ts:
        parts.append(generate_timestamp_suffix())
    
    # Crear el nombre final
    if parts:
        filename = f"{base_name}-{'-'.join(parts)}.png"
    else:
        filename = f"{base_name}.png"
    
    return os.path.join(output_dir, filename)

def parse_tuple_column(tuple_str):
    """
    Parsea una columna que contiene tuplas en formato string.
    """
    try:
        # Remover espacios iniciales y finales, luego paréntesis
        clean_str = tuple_str.strip().strip('()')
        values = [float(x.strip()) for x in clean_str.split(',')]
        return values
    except:
        return [np.nan, np.nan, np.nan]

def load_statistics_data(file_path, parse_tuples=False):
    """
    Carga y procesa los datos de estadísticas del algoritmo genético.
    
    Args:
        file_path: Ruta al archivo CSV de estadísticas
        parse_tuples: Si True, parsea las columnas como tuplas (para datos lexicográficos).
                     Si False, trata las columnas como valores numéricos simples.
    """
    # Definir nombres de columnas basados en la estructura observada
    column_names = [
        'generation',
        'population_size', 
        'worst_lexical_fitness',
        'best_lexical_fitness',
        'fitness_median',
        'fitness_mean',
        'fitness_std'
    ]
    
    if parse_tuples:
        # Cargar datos usando una expresión regular que no separe dentro de paréntesis
        # Usamos sep con una regex que busca comas que NO estén dentro de paréntesis
        df = pd.read_csv(file_path, names=column_names, sep=r',(?![^()]*\))', engine='python')
        
        # Parsear las tuplas de estadísticas de fitness
        # Cada tupla contiene: (victorias + 0.5*empates, tiempo_medio_ganar, tiempo_medio_perder)
        # Solo nos interesa el primer valor (victorias + 0.5*empates)
        worst_fitness_parsed = df['worst_lexical_fitness'].apply(parse_tuple_column)
        best_fitness_parsed = df['best_lexical_fitness'].apply(parse_tuple_column)

        # Extraer solo el primer valor de cada tupla (fitness real)
        df['worst_victories_fitness'] = [x[0] if len(x) > 0 else np.nan for x in worst_fitness_parsed]
        df['best_victories_fitness'] = [x[0] if len(x) > 0 else np.nan for x in best_fitness_parsed]
        
        # Determinar min y max del fitness real de ambas tuplas
        # Crear una lista de todos los valores de fitness válidos para cada generación
        fitness_values = []
        for i, row in df.iterrows():
            gen_values = []
            if not pd.isna(row['worst_victories_fitness']):
                gen_values.append(row['worst_victories_fitness'])
            if not pd.isna(row['best_victories_fitness']):
                gen_values.append(row['best_victories_fitness'])
            fitness_values.append(gen_values)
        
        # Calcular min y max reales
        df['fitness_min'] = [min(vals) if vals else np.nan for vals in fitness_values]
        df['fitness_max'] = [max(vals) if vals else np.nan for vals in fitness_values]
        
        # Si no hay valores válidos de min/max, usar estimaciones basadas en media y desviación estándar
        df['fitness_min'] = df['fitness_min'].fillna(df['fitness_mean'] - df['fitness_std'])
        df['fitness_max'] = df['fitness_max'].fillna(df['fitness_mean'] + df['fitness_std'])
        
    else:
        # Cargar datos como valores numéricos simples (separados por comas normales)
        df = pd.read_csv(file_path, names=column_names, sep=',')
        
        # Convertir a numérico, manejando posibles errores
        numeric_columns = ['worst_lexical_fitness', 'best_lexical_fitness', 'fitness_median', 'fitness_mean', 'fitness_std']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Para datos no-tupla, asumir que worst/best ya son los valores mínimos/máximos
        df['worst_victories_fitness'] = df['worst_lexical_fitness']
        df['best_victories_fitness'] = df['best_lexical_fitness']
        df['fitness_min'] = df['worst_lexical_fitness']
        df['fitness_max'] = df['best_lexical_fitness']
    
    return df

def create_fitness_evolution_plot(df, output_dir='imagenes'):
    """
    Crea una visualización completa de la evolución del fitness.
    """
    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(exist_ok=True)
    
    # Configurar la figura
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Evolución del Fitness por Generación', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Líneas de tendencia de todas las métricas
    ax1 = axes[0, 0]
    ax1.plot(df['generation'], df['worst_victories_fitness'], 'o-', label='Mínimo', linewidth=2, markersize=4)
    ax1.plot(df['generation'], df['best_victories_fitness'], 's-', label='Máximo', linewidth=2, markersize=4)
    ax1.plot(df['generation'], df['fitness_median'], '^-', label='Mediana', linewidth=2, markersize=4)
    ax1.plot(df['generation'], df['fitness_mean'], 'd-', label='Media', linewidth=2, markersize=4)
    
    ax1.set_xlabel('Generación')
    ax1.set_ylabel('Fitness')
    ax1.set_title('Tendencias de Fitness')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Gráfico 2: Área sombreada mostrando rango (min-max) con media
    ax2 = axes[0, 1]
    ax2.fill_between(df['generation'], df['worst_victories_fitness'], df['best_victories_fitness'], 
                     alpha=0.4, color='lightblue', label='Rango (Min-Max)')
    ax2.plot(df['generation'], df['fitness_mean'], 'ro-', label='Media', linewidth=2)
    ax2.plot(df['generation'], df['fitness_median'], 'go-', label='Mediana', linewidth=2)
    
    ax2.set_xlabel('Generación')
    ax2.set_ylabel('Fitness')
    ax2.set_title('Rango de Fitness con Tendencias Centrales')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Gráfico 3: Desviación estándar con barras de error
    ax3 = axes[1, 0]
    ax3.errorbar(df['generation'], df['fitness_mean'], yerr=df['fitness_std'], 
                 fmt='o-', capsize=5, capthick=2, elinewidth=2, 
                 label='Media ± Desv. Estándar')
    ax3.plot(df['generation'], df['fitness_median'], 's-', label='Mediana', linewidth=2)
    
    ax3.set_xlabel('Generación')
    ax3.set_ylabel('Fitness')
    ax3.set_title('Media con Desviación Estándar')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Gráfico 4: Evolución de la desviación estándar
    ax4 = axes[1, 1]
    ax4.plot(df['generation'], df['fitness_std'], 'o-', linewidth=2, markersize=6, color='orange')
    ax4.fill_between(df['generation'], 0, df['fitness_std'], alpha=0.3, color='orange')
    
    ax4.set_xlabel('Generación')
    ax4.set_ylabel('Desviación Estándar')
    ax4.set_title('Evolución de la Dispersión')
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    plt.tight_layout()
    
    # Guardar la figura
    output_path = create_filename('fitness_evolution_complete', output_dir)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfica guardada en: {output_path}")
    
    return fig

def create_single_comprehensive_plot(df, output_dir='imagenes'):
    """
    Crea una sola gráfica comprehensiva con todas las métricas.
    """
    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(exist_ok=True)
    
    # Configurar la figura
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Área sombreada para el rango min-max
    ax.fill_between(df['generation'], df['worst_victories_fitness'], df['best_victories_fitness'], 
                    alpha=0.4, color='lightblue', label='Rango (Min-Max)')
    
    # Líneas principales
    ax.plot(df['generation'], df['worst_victories_fitness'], 'v-', label='Mínimo', 
            linewidth=2.5, markersize=6, color='red')
    ax.plot(df['generation'], df['best_victories_fitness'], '^-', label='Máximo', 
            linewidth=2.5, markersize=6, color='green')
    ax.plot(df['generation'], df['fitness_median'], 's-', label='Mediana', 
            linewidth=2.5, markersize=6, color='blue')
    ax.plot(df['generation'], df['fitness_mean'], 'o-', label='Media', 
            linewidth=3, markersize=7, color='orange')
    
    # Barras de error para la desviación estándar (solo cada pocas generaciones para claridad)
    step = max(1, len(df) // 10)  # Mostrar error bars cada 10% de los datos
    error_indices = range(0, len(df), step)
    ax.errorbar(df['generation'].iloc[error_indices], 
                df['fitness_mean'].iloc[error_indices],
                yerr=df['fitness_std'].iloc[error_indices],
                fmt='none', ecolor='orange', alpha=0.6, capsize=4, 
                label='Desv. Estándar')
    
    # Configuración del gráfico
    ax.set_xlabel('Generación', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fitness', fontsize=12, fontweight='bold')
    ax.set_title('Evolución del Fitness', 
                 fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Mejorar la apariencia
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Guardar la figura
    output_path = create_filename('fitness_evolution_unified', output_dir)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfica unificada guardada en: {output_path}")
    
    return fig

def create_std_deviation_plot(df, output_dir='imagenes'):
    """
    Crea una visualización independiente de la evolución de la desviación estándar.
    """
    # Crear directorio de salida si no existe
    Path(output_dir).mkdir(exist_ok=True)
    
    # Configurar la figura
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Gráfico de desviación estándar con color amarillo
    ax.plot(df['generation'], df['fitness_std'], 'o-', linewidth=3, markersize=8, color='orange')
    ax.fill_between(df['generation'], 0, df['fitness_std'], alpha=0.4, color='orange')

    # Configuración del gráfico
    ax.set_xlabel('Generación', fontsize=12, fontweight='bold')
    ax.set_ylabel('Desviación Estándar', fontsize=12, fontweight='bold')
    ax.set_title('Evolución de la Dispersión del Fitness', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    # Mejorar la apariencia
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    # Guardar la figura
    output_path = create_filename('fitness_std_evolution', output_dir)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Gráfica de desviación estándar guardada en: {output_path}")
    
    return fig

def print_summary_statistics(df):
    """
    Imprime estadísticas resumidas de la evolución.
    """
    print("\n" + "="*70)
    print("RESUMEN DE LA EVOLUCIÓN DEL FITNESS")
    print("Fitness = victorias + 0.5 * empates")
    print("="*70)
    
    print(f"Número de generaciones: {len(df)}")
    print(f"Fitness inicial (Gen {df['generation'].iloc[0]}):")
    print(f"  - Min: {df['worst_victories_fitness'].iloc[0]:.3f}")
    print(f"  - Max: {df['best_victories_fitness'].iloc[0]:.3f}")
    print(f"  - Media: {df['fitness_mean'].iloc[0]:.3f}")
    print(f"  - Mediana: {df['fitness_median'].iloc[0]:.3f}")
    print(f"  - Desv. Std: {df['fitness_std'].iloc[0]:.3f}")
    
    print(f"\nFitness final (Gen {df['generation'].iloc[-1]}):")
    print(f"  - Min: {df['worst_victories_fitness'].iloc[-1]:.3f}")
    print(f"  - Max: {df['best_victories_fitness'].iloc[-1]:.3f}")
    print(f"  - Media: {df['fitness_mean'].iloc[-1]:.3f}")
    print(f"  - Mediana: {df['fitness_median'].iloc[-1]:.3f}")
    print(f"  - Desv. Std: {df['fitness_std'].iloc[-1]:.3f}")
    
    print(f"\nMejora total:")
    mejora_media = df['fitness_mean'].iloc[-1] - df['fitness_mean'].iloc[0]
    mejora_max = df['best_victories_fitness'].iloc[-1] - df['best_victories_fitness'].iloc[0]
    print(f"  - Media: {mejora_media:+.3f}")
    print(f"  - Máximo: {mejora_max:+.3f}")
    
    print("="*60)

def main(file_path=None, parse_tuples=False):
    """
    Función principal que procesa un archivo específico de estadísticas y genera visualizaciones.
    
    Args:
        file_path: Ruta al archivo de estadísticas CSV. Si no se proporciona, se toma de sys.argv[1]
        parse_tuples: Si True, parsea las columnas como tuplas (para datos lexicográficos).
                     Si False, trata las columnas como valores numéricos simples.
    """
    # Obtener la ruta del archivo
    if file_path is None:
        if len(sys.argv) < 2:
            print("Error: Debes proporcionar la ruta al archivo de estadísticas.")
            print("\nUso:")
            print(f"  python {sys.argv[0]} <ruta_al_archivo_csv> [--no-tuples]")
            print("\nEjemplo:")
            print(f"  python {sys.argv[0]} /ruta/a/inspyred-statistics-file-20241024-123456.csv")
            print(f"  python {sys.argv[0]} /ruta/a/stats.csv --no-tuples  # Para datos numéricos simples")
            return
        file_path = sys.argv[1]
        
        # Verificar si se especifica --no-tuples
        if len(sys.argv) > 2 and '--no-tuples' in sys.argv:
            parse_tuples = False
    
    # Verificar que el archivo existe
    if not os.path.exists(file_path):
        print(f"Error: El archivo '{file_path}' no existe.")
        return
    
    print(f"Procesando archivo: {file_path}")
    print(f"Modo de parseo: {'Tuplas lexicográficas' if parse_tuples else 'Valores numéricos simples'}")
    
    # Cargar y procesar datos
    try:
        df = load_statistics_data(file_path, parse_tuples=parse_tuples)
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return
    
    # Imprimir resumen
    print_summary_statistics(df)
    
    # Crear visualizaciones
    print("\nGenerando visualizaciones...")
    
    # Gráfica completa (múltiples subplots)
    fig1 = create_fitness_evolution_plot(df)
    
    # Gráfica unificada
    fig2 = create_single_comprehensive_plot(df)
    
    # Gráfica independiente de desviación estándar
    fig3 = create_std_deviation_plot(df)
    
    # Mostrar las gráficas
    plt.show()
    
    print("\n¡Visualizaciones completadas!")
    print(f"Archivo procesado: {file_path}")
    print(f"\nConfiguración de archivos:")
    print(f"  - Sufijo personalizado: '{FILE_SUFFIX}'")
    print(f"  - Usar timestamp: {USE_TIMESTAMP}")
    print(f"  - Directorio de salida: imagenes/")
    print(f"\nPara cambiar el nombrado de archivos, modifica las variables:")
    print(f"  FILE_SUFFIX y USE_TIMESTAMP al inicio del script")

if __name__ == "__main__":
    main()
