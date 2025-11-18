#!/usr/bin/env python3
"""
Script para procesar en batch todos los archivos de estadísticas de carpetas GABotsLit.
Genera visualizaciones de fitness para cada experimento encontrado.
"""

import os
import glob
from pathlib import Path
import sys

# Importar las funciones del script principal
import fitness_generaciones as fg

def find_statistics_files(base_dir='../resultados', folder_prefix='GABotsLit'):
    """
    Busca todos los archivos inspyred-statistics-file-*.csv en carpetas que coincidan con el prefijo.
    
    Args:
        base_dir: Directorio base donde buscar
        folder_prefix: Prefijo de las carpetas a procesar
        
    Returns:
        Lista de tuplas (folder_name, file_path)
    """
    results = []
    
    # Obtener ruta absoluta del directorio base
    base_path = Path(__file__).parent / base_dir
    base_path = base_path.resolve()
    
    # Buscar todas las carpetas que coincidan con el prefijo
    pattern = str(base_path / f"{folder_prefix}*")
    matching_folders = glob.glob(pattern)
    
    for folder in matching_folders:
        if os.path.isdir(folder):
            # Buscar archivos de estadísticas dentro de la carpeta
            stats_pattern = os.path.join(folder, 'inspyred-statistics-file-*.csv')
            stats_files = glob.glob(stats_pattern)
            
            for stats_file in stats_files:
                folder_name = os.path.basename(folder)
                results.append((folder_name, stats_file))
    
    return results

def process_all_experiments(folder_prefix='GABotsLit', parse_tuples=False, output_dir='imagenes'):
    """
    Procesa todos los experimentos encontrados y genera visualizaciones.
    
    Args:
        folder_prefix: Prefijo de las carpetas a buscar
        parse_tuples: Si True, parsea columnas como tuplas lexicográficas
        output_dir: Directorio donde guardar las imágenes
    """
    # Buscar archivos
    print("="*70)
    print(f"Buscando archivos de estadísticas en carpetas {folder_prefix}*...")
    print("="*70)
    
    files = find_statistics_files(folder_prefix=folder_prefix)
    
    if not files:
        print(f"No se encontraron archivos de estadísticas en carpetas {folder_prefix}*")
        return
    
    print(f"\nEncontrados {len(files)} archivo(s) de estadísticas:\n")
    for folder_name, file_path in files:
        print(f"  - {folder_name}: {os.path.basename(file_path)}")
    
    # Crear directorio de salida
    output_path = Path(__file__).parent / output_dir
    output_path.mkdir(exist_ok=True)
    
    # Procesar cada archivo
    print("\n" + "="*70)
    print("Procesando archivos...")
    print("="*70)
    
    for idx, (folder_name, file_path) in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] Procesando {folder_name}...")
        print(f"Archivo: {os.path.basename(file_path)}")
        
        try:
            # Cargar datos
            df = fg.load_statistics_data(file_path, parse_tuples=parse_tuples)
            
            # Modificar FILE_SUFFIX temporalmente
            original_suffix = fg.FILE_SUFFIX
            original_timestamp = fg.USE_TIMESTAMP
            
            fg.FILE_SUFFIX = folder_name
            fg.USE_TIMESTAMP = False
            
            # Generar visualizaciones (sin mostrar)
            import matplotlib.pyplot as plt
            plt.ioff()  # Desactivar modo interactivo
            
            fg.create_fitness_evolution_plot(df, output_dir=str(output_path))
            fg.create_single_comprehensive_plot(df, output_dir=str(output_path))
            fg.create_std_deviation_plot(df, output_dir=str(output_path))
            
            plt.close('all')  # Cerrar todas las figuras
            
            # Restaurar configuración original
            fg.FILE_SUFFIX = original_suffix
            fg.USE_TIMESTAMP = original_timestamp
            
            print(f"✓ Completado: {folder_name}")
            
        except Exception as e:
            print(f"✗ Error procesando {folder_name}: {e}")
            continue
    
    print("\n" + "="*70)
    print("¡Procesamiento completado!")
    print("="*70)
    print(f"Imágenes guardadas en: {output_path}")

def main():
    """
    Función principal del script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Procesa en batch archivos de estadísticas y genera visualizaciones.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Procesar todas las carpetas GABotsLit con datos numéricos simples
  python batch_fitness_visualizations.py
  
  # Procesar carpetas con prefijo personalizado
  python batch_fitness_visualizations.py --prefix CoEvELO
  
  # Procesar con datos de tuplas lexicográficas
  python batch_fitness_visualizations.py --tuples
  
  # Guardar en directorio personalizado
  python batch_fitness_visualizations.py --output mi_directorio
        """
    )
    
    parser.add_argument(
        '--prefix',
        default='GABotsLit',
        help='Prefijo de las carpetas a buscar (default: GABotsLit)'
    )
    
    parser.add_argument(
        '--tuples',
        action='store_true',
        help='Parsear columnas como tuplas lexicográficas'
    )
    
    parser.add_argument(
        '--output',
        default='imagenes',
        help='Directorio de salida para las imágenes (default: imagenes)'
    )
    
    args = parser.parse_args()
    
    # Procesar experimentos
    process_all_experiments(
        folder_prefix=args.prefix,
        parse_tuples=args.tuples,
        output_dir=args.output
    )

if __name__ == "__main__":
    main()
