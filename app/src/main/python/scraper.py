import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def main():
    try:
        # URL del sitio web
        url = "https://boxn8.com.br/wod/"
        
        # Realizar la solicitud HTTP
        response = requests.get(url)
        response.raise_for_status()  # Lanza una excepción si hay error HTTP
        
        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar el contenedor principal del WOD
        wod_container = soup.find('div', class_='entry-content')
        
        if not wod_container:
            return "No se encontró el contenedor del WOD"
        
        # Extraer el texto del WOD
        wod_text = wod_container.get_text(strip=True)
        
        # Formatear el texto
        wod_text = re.sub(r'\s+', ' ', wod_text)  # Reemplazar múltiples espacios por uno solo
        
        # Obtener la fecha actual
        current_date = datetime.now().strftime("%d/%m/%Y")
        
        # Formatear la salida
        formatted_output = f"📅 Box N8 - {current_date}\n"
        formatted_output += "=" * 30 + "\n"
        formatted_output += wod_text + "\n"
        
        return formatted_output
        
    except requests.RequestException as e:
        return f"Error al obtener el WOD: {str(e)}"
    except Exception as e:
        return f"Error inesperado: {str(e)}"

if __name__ == "__main__":
    print(main())