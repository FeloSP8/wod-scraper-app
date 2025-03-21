import os
import sys
from com.chaquo.python import Python

def main():
    result = "🏋️ WOD Scraper Unificado\n"
    result += "=" * 50 + "\n"

    try:
        # Get the app files directory
        app_files_dir = str(Python.getPlatform().getApplication().getFilesDir())

        # Import the modules directly instead of using subprocess
        result += "\n📦 Ejecutando N8 scraper...\n"
        import scraper
        scraper_result = scraper.main()
        result += f"{scraper_result}\n"

        result += "\n📦 Ejecutando CrossfitDB scraper...\n"
        import crossfitdb
        crossfitdb_result = crossfitdb.main(semana=True)
        result += f"{crossfitdb_result}\n"

        result += "\n✅ Proceso finalizado correctamente"
        return result

    except Exception as e:
        result += f"\n❌ Error en el scraper: {str(e)}"
        return result

if __name__ == "__main__":
    print(main())