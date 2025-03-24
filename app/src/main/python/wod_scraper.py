import sys
import os
from datetime import datetime

def main(include_weekends=False):
    result = ""
    
    try:
        # Import the modules directly instead of using subprocess
        result += "📱 Obteniendo WODs de CrossFit DB...\n"
        import crossfitdb
        crossfitdb_result = crossfitdb.main(include_weekends)
        result += f"{crossfitdb_result}\n"
        
        # Import the modules directly instead of using subprocess
        result += "\n📱 Obteniendo WODs de N8...\n"
        import n8
        scraper_result = n8.main(include_weekends)
        result += f"{scraper_result}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error al obtener WODs: {str(e)}"

if __name__ == "__main__":
    # Si se ejecuta directamente, procesar argumentos
    import argparse
    parser = argparse.ArgumentParser(description='Obtener WODs de CrossFit DB y N8')
    parser.add_argument('--weekends', action='store_true', help='Incluir fines de semana')
    args = parser.parse_args()
    
    # Ejecutar el script
    result = main(args.weekends)
    print(result)