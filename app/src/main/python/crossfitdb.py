import requests
import json
import sys
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
import argparse  # Para procesar argumentos de línea de comandos
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Importar configuración desde archivo externo
try:
    from config import CROSSFITDB_CONFIG, EMAIL_CONFIG
    print("Configuración de CrossFitDB y correo cargada correctamente")
except ImportError:
    print("ERROR: No se encuentra el archivo config.py")
    print("Por favor, copia config.example.py a config.py y configura tus datos")
    print("Consulta el README para más información")
    sys.exit(1)

# Función para obtener la fecha en formato DD-MM-YYYY
def formatear_fecha(fecha):
    return fecha.strftime("%d-%m-%Y")

# Función para obtener el rango de la semana actual (lunes a viernes)
def obtener_rango_semana_actual():
    hoy = datetime.now()
    
    # Si es domingo, siempre obtener el rango de la próxima semana
    if hoy.weekday() == 6:  # 6 = domingo
        lunes = hoy + timedelta(days=1)  # El siguiente lunes
    else:
        # Para otros días, obtener el lunes de la semana actual
        dias_hasta_lunes = hoy.weekday()
        lunes = hoy - timedelta(days=dias_hasta_lunes)
    
    viernes = lunes + timedelta(days=4)  # 4 días después del lunes = viernes
    return lunes, viernes

# Función para limpiar texto HTML preservando estructura
def limpiar_html(texto):
    if not texto:
        return ""
    
    # Reemplazar algunos tags HTML con sus equivalentes en texto plano
    texto = texto.replace("<br>", "\n").replace("<br />", "\n").replace("<br/>", "\n")
    texto = texto.replace("<p>", "").replace("</p>", "\n")
    texto = texto.replace("<h1>", "").replace("</h1>", "\n")
    texto = texto.replace("<h2>", "").replace("</h2>", "\n")
    texto = texto.replace("<h3>", "").replace("</h3>", "\n")
    
    # Preservar listas pero sin añadir bullets
    texto = texto.replace("<ul>", "").replace("</ul>", "")
    texto = texto.replace("<ol>", "").replace("</ol>", "")
    texto = texto.replace("<li>", "</li>", "\n")
    
    # Usar BeautifulSoup para eliminar cualquier otro tag HTML
    soup = BeautifulSoup(texto, "html.parser")
    texto_limpio = soup.get_text(separator=" ")
    
    # Eliminar bullets y guiones al inicio de cada línea, pero mantener letras con punto
    lineas = texto_limpio.split('\n')
    lineas_limpias = []
    for linea in lineas:
        # Solo eliminar bullets (•) y guiones (-, –, —)
        linea = re.sub(r'^[•·]|\s*[-–—]\s*', '', linea.strip())
        if linea:  # Solo mantener líneas con contenido
            lineas_limpias.append(linea)
    
    texto_limpio = '\n'.join(lineas_limpias)
    
    # Eliminar líneas vacías múltiples (mantener máximo 2 saltos de línea)
    texto_limpio = re.sub(r'\n{3,}', '\n\n', texto_limpio)
    
    # Eliminar espacios en blanco múltiples
    texto_limpio = re.sub(r' +', ' ', texto_limpio)
    
    return texto_limpio.strip()

# Función para crear y guardar un documento HTML
def guardar_html(titulo, contenido_html, nombre_archivo):
    # Plantilla HTML básica
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{titulo}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .wod-content {{
            background-color: #f9f9f9;
            border-left: 4px solid #444;
            padding: 15px;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 0.8em;
            color: #777;
        }}
    </style>
</head>
<body>
    <h1>{titulo}</h1>
    <div class="wod-content">
        {contenido_html}
    </div>
    <div class="footer">
        Generado por WOD Scraper CrossFit - {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
</body>
</html>"""

    # Crear el directorio de salida si no existe
    os.makedirs('exports', exist_ok=True)
    
    # Guardar el archivo HTML
    ruta_completa = os.path.join('exports', nombre_archivo)
    with open(ruta_completa, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ Documento HTML guardado en: {ruta_completa}")
    return ruta_completa

# Lista de palabras que siempre deben aparecer en mayúsculas
PALABRAS_MAYUSCULAS = [
    "wod",
    "amrap",
    "emom",
    "rx",
    "tabata",
    "du",
    "ygig",
    "c2b",
    "t2b",
    "sc",
    "kbsr",
]

# Lista de palabras que identifican un tipo de entrenamiento 
TIPOS_ENTRENAMIENTO = [
    "amrap",
    "emom",
    "tabata",
    "metcon",
    "for time",
    "strength",
    "skill olympics",
    "skill",
    "etabata"
]

# Función para aplicar formato al texto
def aplicar_formato(texto, dia_semana="", fecha_formateada=""):
    # Dividir el texto en líneas para preservar la estructura
    lineas = texto.split("\n")
    lineas_formateadas = []
    
    # Verificar si la primera línea contiene "wod" y la fecha/día
    if lineas and re.search(r'^wod\s+', lineas[0].lower()):
        # Saltamos la primera línea pues ya la mostraremos en el título
        lineas = lineas[1:]
    
    for linea in lineas:
        # Si la línea está vacía, la conservamos igual
        if not linea.strip():
            lineas_formateadas.append("")
            continue
        
        # Mantener el formato original de la línea
        lineas_formateadas.append(linea)
    
    # Unir las líneas en un texto
    texto_formateado = '\n'.join(lineas_formateadas)
    
    # Reducir saltos de línea excesivos
    texto_formateado = re.sub(r'\n{3,}', '\n\n', texto_formateado)
    
    return texto_formateado

# Función para obtener el contenido del whiteboard del WOD
def obtener_wod_whiteboard(id_wod, session_token):
    print(f"\nObteniendo whiteboard para WOD ID: {id_wod}...")
    
    url_whiteboard = "https://sport.nubapp.com/api/v4/wods/getWodWhiteboard.php"
    
    payload_whiteboard = {
        "u": "ionic",
        "p": "ed24ec82ce9631b5bcf4e06e3bdbe60d",
        "app_version": "5.09.09",
        "id_application": CROSSFITDB_CONFIG["id_application"],
        "id_user": CROSSFITDB_CONFIG["id_user"],
        "id_wod": id_wod,
        "token": session_token
    }
    
    try:
        # Hacer la petición
        response = requests.post(url_whiteboard, data=payload_whiteboard, headers=headers)
        response.raise_for_status()
        
        # Verificar la respuesta
        whiteboard_data = response.json()
        
        # Imprimir respuesta para depuración
        print("Respuesta del whiteboard (resumida):")
        if "data" in whiteboard_data:
            print(f"Contiene datos: {len(json.dumps(whiteboard_data['data']))} caracteres")
        else:
            print(json.dumps(whiteboard_data, indent=4, ensure_ascii=False))
        
        # Guardar la respuesta original para depuración si es necesario
        html_content = None
        
        # Extraer contenido HTML según la estructura vista en el ejemplo
        if "data" in whiteboard_data and "wod_whiteboard" in whiteboard_data["data"]:
            wod_whiteboard = whiteboard_data["data"]["wod_whiteboard"]
            if wod_whiteboard and len(wod_whiteboard) > 0:
                if "benchmark" in wod_whiteboard[0] and "description_html" in wod_whiteboard[0]["benchmark"]:
                    html_content = wod_whiteboard[0]["benchmark"]["description_html"]
                    print("✅ HTML encontrado en data.wod_whiteboard[0].benchmark.description_html")
                    
                    # Guardar la respuesta completa para análisis si es necesario
                    if id_wod == "244419":  # Si es el ID específico que estamos monitoreando
                        os.makedirs('exports', exist_ok=True)
                        # Eliminar el archivo si ya existe y crear uno nuevo
                        ruta_json = f'exports/respuesta_wod_{id_wod}.json'
                        try:
                            if os.path.exists(ruta_json):
                                os.remove(ruta_json)
                            # Escribir la respuesta JSON
                            with open(ruta_json, 'w', encoding='utf-8') as f:
                                json.dump(whiteboard_data, f, indent=4, ensure_ascii=False)
                            print(f"✅ Respuesta completa guardada en {ruta_json}")
                        except Exception as e:
                            print(f"⚠️ Error al guardar archivo JSON: {e}")
                    
                    return html_content
        
        # Si no se encontró en la ruta principal, buscar en ubicaciones alternativas
        print("⚠️ No se encontró el campo description_html en la ruta principal. Buscando alternativas...")
        
        # 1. Buscar en otros elementos de wod_whiteboard si existen
        if "data" in whiteboard_data and "wod_whiteboard" in whiteboard_data["data"]:
            for item in whiteboard_data["data"]["wod_whiteboard"]:
                # Buscar en benchmark
                if "benchmark" in item:
                    for key in ["description_html", "content_html", "html", "content", "description"]:
                        if key in item["benchmark"]:
                            html_content = item["benchmark"][key]
                            print(f"✅ HTML encontrado en data.wod_whiteboard[i].benchmark.{key}")
                            return html_content
                
                # Buscar directamente en el item
                for key in ["description_html", "content_html", "html", "content", "description"]:
                    if key in item:
                        html_content = item[key]
                        print(f"✅ HTML encontrado en data.wod_whiteboard[i].{key}")
                        return html_content
        
        # 2. Explorar otras posibles ubicaciones del contenido HTML
        if "data" in whiteboard_data:
            # Buscar en campos que puedan contener HTML
            for key in ["content_html", "html", "content", "description", "description_html"]:
                if key in whiteboard_data["data"]:
                    html_content = whiteboard_data["data"][key]
                    print(f"✅ HTML encontrado en data.{key}")
                    return html_content
            
            # Si hay un campo 'wod', buscar también allí
            if "wod" in whiteboard_data["data"]:
                for key in ["description_html", "content_html", "html", "content", "description"]:
                    if key in whiteboard_data["data"]["wod"]:
                        html_content = whiteboard_data["data"]["wod"][key]
                        print(f"✅ HTML encontrado en data.wod.{key}")
                        return html_content
        
        # Si llegamos aquí y no encontramos nada, guardamos la respuesta para análisis
        print("⚠️ No se encontró ningún contenido HTML en la respuesta")
        # Crear el directorio exports si no existe
        os.makedirs('exports', exist_ok=True)
        # Eliminar el archivo si ya existe y crear uno nuevo
        ruta_json = f'exports/error_respuesta_wod_{id_wod}.json'
        try:
            if os.path.exists(ruta_json):
                os.remove(ruta_json)
            # Escribir la respuesta JSON
            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(whiteboard_data, f, indent=4, ensure_ascii=False)
            print(f"⚠️ Respuesta sin HTML guardada en {ruta_json} para análisis")
        except Exception as e:
            print(f"⚠️ Error al guardar archivo JSON de error: {e}")
        
        return None
    
    except Exception as e:
        print(f"❌ Error al obtener whiteboard con id_wod={id_wod}: {e}")
        
        # Intentar una segunda dirección URL alternativa si falla la primera
        try:
            url_whiteboard_alt = "https://sport.nubapp.com/api/v4/activities/getWod.php"
            print(f"Intentando con URL alternativa: {url_whiteboard_alt}")
            
            response = requests.post(url_whiteboard_alt, data=payload_whiteboard, headers=headers)
            response.raise_for_status()
            
            whiteboard_data = response.json()
            
            if "data" in whiteboard_data and "description" in whiteboard_data["data"]:
                print("✅ Se encontró contenido en la URL alternativa")
                return whiteboard_data["data"]["description"]
            else:
                return None
        except Exception as e2:
            print(f"❌ También falló el intento alternativo: {e2}")
            return None

# Función para obtener un WOD para una fecha específica
def obtener_wod_para_fecha(fecha, session_token, exportar_html=False):
    fecha_formateada = formatear_fecha(fecha)
    print(f"\nConsultando actividades para la fecha: {fecha_formateada}")
    
    url_calendar = "https://sport.nubapp.com/api/v4/activities/getActivitiesCalendar.php"
    
    payload_calendar = {
        "u": "ionic",
        "p": "ed24ec82ce9631b5bcf4e06e3bdbe60d",
        "app_version": "5.09.09",
        "id_application": CROSSFITDB_CONFIG["id_application"],
        "id_user": CROSSFITDB_CONFIG["id_user"],
        "start_timestamp": fecha_formateada,
        "end_timestamp": fecha_formateada,
        "id_category_activit": "111",
        "token": session_token
    }
    
    try:
        print(f"Haciendo request a {url_calendar} con payload:")
        print(json.dumps(payload_calendar, indent=2))
        response_calendar = requests.post(url_calendar, data=payload_calendar, headers=headers)
        print(f"Status code: {response_calendar.status_code}")
        print("Respuesta:")
        print(json.dumps(response_calendar.json(), indent=2))
        response_calendar.raise_for_status()
        calendar_data = response_calendar.json()
        
        if "data" in calendar_data and "activities_calendar" in calendar_data["data"]:
            activities = calendar_data["data"]["activities_calendar"]
            print(f"Actividades encontradas: {len(activities)}")
            for activity in activities:
                print(f"Actividad: {json.dumps(activity, indent=2)}")
            workout_activities = [activity for activity in activities if activity.get("name_activity") == "WORKOUT OF THE DAY"]
            print(f"WODs encontrados: {len(workout_activities)}")
            
            if workout_activities:
                wod_activity = workout_activities[0]
                id_activity_calendar = wod_activity.get("id_activity_calendar")
                print(f"ID de actividad encontrado: {id_activity_calendar}")
                
                url_wod_details = "https://sport.nubapp.com/api/v4/activities/getUserActivityCalendar.php"
                
                payload_wod_details = {
                    "u": "ionic",
                    "p": "ed24ec82ce9631b5bcf4e06e3bdbe60d",
                    "app_version": "5.09.09",
                    "id_application": CROSSFITDB_CONFIG["id_application"],
                    "id_user": CROSSFITDB_CONFIG["id_user"],
                    "id_activity_calendar": id_activity_calendar,
                    "token": session_token
                }
                
                print(f"\nHaciendo request a {url_wod_details} con payload:")
                print(json.dumps(payload_wod_details, indent=2))
                response_wod = requests.post(url_wod_details, data=payload_wod_details, headers=headers)
                print(f"Status code: {response_wod.status_code}")
                print("Respuesta:")
                print(json.dumps(response_wod.json(), indent=2))
                response_wod.raise_for_status()
                wod_data = response_wod.json()
                
                id_wod = None
                
                if "data" in wod_data:
                    if "id_wod" in wod_data["data"]:
                        id_wod = wod_data["data"].get("id_wod")
                    elif "activity_calendar" in wod_data["data"] and "id_wod" in wod_data["data"]["activity_calendar"]:
                        id_wod = wod_data["data"]["activity_calendar"].get("id_wod")
                    elif "wod" in wod_data["data"] and "id_wod" in wod_data["data"]["wod"]:
                        id_wod = wod_data["data"]["wod"].get("id_wod")
                    elif "id_wod" in wod_data:
                        id_wod = wod_data.get("id_wod")
                    else:
                        for key in wod_data["data"]:
                            if ('id' in key.lower() and 'wod' in key.lower()) or key == "id":
                                id_wod = wod_data["data"][key]
                                break
                
                if id_wod is None:
                    id_wod = id_activity_calendar
                
                if id_wod:
                    url_wod_content = "https://sport.nubapp.com/api/v4/wods/getWodWhiteboard.php"
                    
                    payload_wod_content = {
                        "u": "ionic",
                        "p": "ed24ec82ce9631b5bcf4e06e3bdbe60d",
                        "app_version": "5.09.09",
                        "id_application": CROSSFITDB_CONFIG["id_application"],
                        "id_user": CROSSFITDB_CONFIG["id_user"],
                        "id_wod": id_wod,
                        "token": session_token
                    }
                    
                    response_wod_content = requests.post(url_wod_content, data=payload_wod_content, headers=headers)
                    response_wod_content.raise_for_status()
                    wod_content_data = response_wod_content.json()
                    
                    if "data" in wod_content_data:
                        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                        wod_dia_semana = dias_semana[fecha.weekday()]
                        fecha_str = fecha.strftime("%d/%m/%Y")
                        
                        # Intentar obtener el contenido del WOD de diferentes ubicaciones
                        wod_titulo = ""
                        wod_descripcion = ""
                        
                        # Buscar en data directamente
                        if "title" in wod_content_data["data"]:
                            wod_titulo = wod_content_data["data"]["title"]
                        if "description" in wod_content_data["data"]:
                            wod_descripcion = wod_content_data["data"]["description"]
                        
                        # Buscar en wod_whiteboard si existe
                        if not wod_descripcion and "wod_whiteboard" in wod_content_data["data"]:
                            whiteboard = wod_content_data["data"]["wod_whiteboard"]
                            if whiteboard and len(whiteboard) > 0:
                                if "benchmark" in whiteboard[0]:
                                    if "title" in whiteboard[0]["benchmark"]:
                                        wod_titulo = whiteboard[0]["benchmark"]["title"]
                                    if "description_html" in whiteboard[0]["benchmark"]:
                                        wod_descripcion = whiteboard[0]["benchmark"]["description_html"]
                                    elif "description" in whiteboard[0]["benchmark"]:
                                        wod_descripcion = whiteboard[0]["benchmark"]["description"]
                        
                        # Si aún no tenemos descripción, intentar con el whiteboard
                        if not wod_descripcion:
                            html_content = obtener_wod_whiteboard(id_wod, session_token)
                            if html_content:
                                wod_descripcion = html_content
                        
                        # Si aún no tenemos descripción, buscar en la respuesta original
                        if not wod_descripcion and "data" in wod_data:
                            if "description" in wod_data["data"]:
                                wod_descripcion = wod_data["data"]["description"]
                            elif "wod" in wod_data["data"] and "description" in wod_data["data"]["wod"]:
                                wod_descripcion = wod_data["data"]["wod"]["description"]
                        
                        # Verificar que tenemos contenido
                        if not wod_descripcion:
                            print(f"No se encontró contenido para el WOD del {wod_dia_semana}")
                            return None
                        
                        # Limpiar y formatear
                        wod_titulo_limpio = limpiar_html(wod_titulo) if wod_titulo else ""
                        wod_descripcion_limpia = limpiar_html(wod_descripcion)
                        wod_descripcion_formateada = aplicar_formato(wod_descripcion_limpia)
                        
                        # Construir el WOD
                        wod_completo = f"WOD DEL {wod_dia_semana} {fecha_str}\n"
                        wod_completo += "=" * 40 + "\n"
                        if wod_titulo_limpio and not wod_titulo_limpio.lower().startswith("wod"):
                            wod_completo += f"{wod_titulo_limpio}\n"
                            wod_completo += "-" * 40 + "\n"
                        wod_completo += wod_descripcion_formateada
                        
                        # Verificar que el contenido no está vacío
                        if not wod_descripcion_formateada.strip():
                            print(f"El contenido del WOD del {wod_dia_semana} está vacío")
                            return None
                        
                        return {
                            "fecha": fecha,
                            "dia_semana": wod_dia_semana,
                            "fecha_formateada": fecha_str,
                            "contenido": wod_descripcion_formateada,
                            "texto_completo": wod_completo,
                            "id_wod": id_wod,
                            "valor_orden": fecha.weekday() + 1
                        }
    
    except Exception as e:
        print(f"Error al obtener WOD para fecha {fecha_formateada}: {e}")
    
    return None

# Función para detectar si una línea es un tipo de entrenamiento
def es_tipo_entrenamiento(linea):
    """Helper function para detectar si una línea es un tipo de entrenamiento"""
    try:
        linea_upper = linea.upper()
        # Lista exacta de tipos de entrenamiento permitidos
        tipos_exactos = ["STRENGTH", "METCON", "SKILL", "SKILL OLYMPICS", "W/UP"]
        
        # Verificar tipos exactos
        for tipo in tipos_exactos:
            if linea_upper.strip() == tipo:
                return True
        
        return False
    except:
        return False

# Función para generar un correo con formato HTML elegante
def formatear_wod_para_correo(contenido):
    if not contenido:
        return ""
        
    CATEGORIAS = {
        "STRENGTH": ["STRENGTH"],
        "METCON": ["METCON"],
        "SKILL": ["SKILL", "SKILL GYMNASTICS", "GYMNASTICS"],
        "SKILL OLYMPICS": ["SKILL OLYMPICS"],
        "W/UP": ["W/UP", "WARM UP", "WARMUP"]
    }
    
    lineas = contenido.split('\n')
    resultado = []
    categoria_actual = None
    
    # Saltamos la primera línea si contiene "Crossfit"
    if lineas and "crossfit" in lineas[0].lower():
        lineas = lineas[1:]
        
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
            
        linea_upper = linea.upper()
        es_categoria = False
        
        # Verificar si la línea es una categoría
        for cat, variaciones in CATEGORIAS.items():
            if any(var == linea_upper for var in variaciones):
                es_categoria = True
                categoria_actual = cat
                # Formato para categorías: fondo gris claro y línea vertical azul delgada
                resultado.append(f'<div style="color: #000000; font-weight: 700; background-color: #f5f5f5; padding: 8px 12px; margin: 10px 0; border-left: 2px solid #2980b9;">{linea_upper}</div>')
                break
                
        if not es_categoria:
            # Si no es categoría, es un ejercicio - mantener formato original
            resultado.append(f'<div style="margin-left: 20px; padding: 5px 0; color: #34495e;">{linea}</div>')
            
    return '\n'.join(resultado)

def enviar_correo_con_wods(wods, lunes_fmt, viernes_fmt):
    if not wods:
        print("No hay WODs para enviar por correo.")
        return
    try:
        base64_file = os.path.join(os.path.dirname(__file__), "logo_db_base64.txt")
        with open(base64_file, "r") as file:
            base64_img = file.read().strip()
        print("✅ Logo base64 leído correctamente")
        print(f"Longitud del base64: {len(base64_img)} caracteres")
    except Exception as e:
        print(f"❌ Error al leer el logo base64: {e}")
        return
    # Crear el mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] =  "CROSSFIT DB - " + f"{EMAIL_CONFIG.get('asunto', 'WODs de la semana')} ({lunes_fmt} - {viernes_fmt})"
    msg['From'] = EMAIL_CONFIG["remitente"]
    msg['To'] = EMAIL_CONFIG["destinatario"]

    # Construir el contenido HTML
    contenido_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>WODs de la semana</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f7fa;
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
            }}
            
            .header img {{
                max-width: 150px;
                height: auto;
                margin-bottom: 10px;
            }}
            
            .header-title {{
                font-size: 28px;
                font-weight: 700;
                color: #2c3e50;
                margin: 10px 0;
            }}
            
            h1 {{
                color: #2c3e50;
                font-size: 24px;
                text-align: center;
                font-weight: 500;
                margin-bottom: 30px;
            }}
            
            h2 {{
                margin: 0;
                padding: 12px 15px;
                color: white;
                font-size: 16px;
                font-weight: 700;
                background-color: #2980b9;
                border-radius: 3px 3px 0 0;
            }}
            
            .wod-card {{
                background-color: white;
                margin-bottom: 30px;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            }}
            
            .wod-content {{
                padding: 20px;
            }}
            
            .section-header {{
                color: #000000;
                background-color: #f5f5f5;
                padding: 8px 12px;
                margin: 10px 0;
                border-left: 2px solid #2980b9;
            }}
            
            .workout-text {{
                margin: 8px 0;
                color: #34495e;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.6;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 30px;
                font-size: 12px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/png;base64,{base64_img}" alt="Crossfit DB Logo" style="max-width: 150px; height: auto; margin-bottom: 10px;">
            <div class="header-title">CROSSFIT DB</div>
        </div>
        <h1>WODs de la semana ({lunes_fmt} - {viernes_fmt})</h1>
    """

    # Agregar cada WOD al contenido
    if wods:
        for wod in wods:
            if wod.get("contenido"):
                titulo = f"WOD DEL {wod['dia_semana']} {wod['fecha_formateada']}"
                contenido_html += f"""
                <div class="wod-card">
                    <h2>{titulo}</h2>
                    <div class="wod-content">
                        {formatear_wod_para_correo(wod['contenido'])}
                    </div>
                </div>
                """
    else:
        contenido_html += '''
        <div class="wod-card">
            <h2>Sin WODs disponibles</h2>
            <div class="wod-content">
                <p>No se encontraron WODs para esta semana.</p>
            </div>
        </div>
        '''

    # Agregar pie de página
    contenido_html += """
        <div class="footer">
            <p>Generado automáticamente — WOD Scraper 2.0</p>
        </div>
    </body>
    </html>
    """

    # Adjuntar el contenido HTML al mensaje
    msg.attach(MIMEText(contenido_html, 'html'))

    try:
        # Configurar conexión SMTP
        server = smtplib.SMTP(EMAIL_CONFIG["servidor_smtp"], EMAIL_CONFIG["puerto_smtp"])
        server.starttls()
        server.login(EMAIL_CONFIG["remitente"], EMAIL_CONFIG["contraseña"])
        
        # Enviar correo
        server.send_message(msg)
        server.quit()
        print("✅ Correo enviado correctamente")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

def main(semana=True, fecha=None, mostrar=False, include_weekends=False):
    try:
        print("Iniciando script...")
        # Verificar conectividad antes de hacer peticiones
        try:
            print("Verificando conexión a Internet...")
            requests.get("https://8.8.8.8", timeout=2)
            print("✅ Conexión a Internet verificada")
        except requests.exceptions.RequestException:
            return "❌ Error: No hay conexión a Internet. Por favor, verifica tu conexión."

        print("Verificando si es fin de semana...")
        # Verificar si es fin de semana
        dia_actual = datetime.now().weekday()  # 0=Lunes, 6=Domingo
        print(f"Día actual: {dia_actual}")
        # Si es sábado y los fines de semana no están habilitados, no ejecutar
        if not include_weekends and dia_actual == 5:  # 5=Sábado
            print("Es sábado y los fines de semana no están habilitados")
            return "ℹ️ No se obtienen WODs los sábados cuando no están habilitados"
        print("No es fin de semana o están habilitados")
        
        print("Configurando argumentos...")
        # Configurar argumentos de línea de comandos
        parser = argparse.ArgumentParser(description='Obtener WODs de CrossFitDB')
        parser.add_argument('--fecha', help='Fecha específica en formato DD-MM-YYYY')
        parser.add_argument('--semana', action='store_true', help='Obtener WODs de toda la semana actual')
        parser.add_argument('--mostrar', action='store_true', help='Solo mostrar los WODs (sin enviar por correo)')
        parser.add_argument('--html', action='store_true', help='Exportar WODs como documentos HTML')
        parser.add_argument('--id-wod', help='ID específico de un WOD para obtener su whiteboard')
        parser.add_argument('--whiteboard', action='store_true', help='Usar el endpoint getWodWhiteboard.php directo con ID 244419')
        
        print("Creando objeto Namespace...")
        # En lugar de usar parser.parse_args(), creamos un objeto Namespace con los argumentos proporcionados
        args = argparse.Namespace(
            fecha=fecha,
            semana=semana,
            mostrar=mostrar,
            html=False,
            id_wod=None,
            whiteboard=False
        )

        print("Verificando configuración...")
        # Verificar configuración
        if not all(key in CROSSFITDB_CONFIG for key in ["username", "password", "id_application"]):
            return "❌ Error: Configuración incompleta en CROSSFITDB_CONFIG"

        print("Configurando headers...")
        global headers
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://localhost/",
            "Referer": "http://localhost/",
            "sec-ch-ua": '"Android WebView";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "Android",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; SM-G988N Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.6045.193 Mobile Safari/537.36",
            "X-Requested-With": "com.Nubapp.CrossFitDB"
        }
        
        # ✅ 1. AUTENTICARSE Y OBTENER TOKEN
        print("📡 Conectando a CrossFitDB...")
        url_auth = "https://sport.nubapp.com/api/v4/users/checkUser.php"
        
        payload_auth = {
            "u": "ionic",
            "p": "ed24ec82ce9631b5bcf4e06e3bdbe60d",
            "app_version": "5.09.09",
            "username": CROSSFITDB_CONFIG["username"],
            "password": CROSSFITDB_CONFIG["password"],
            "platform": "android",
            "id_application": CROSSFITDB_CONFIG["id_application"]
        }

        print("Haciendo request de autenticación...")
        try:
            response_auth = requests.post(url_auth, data=payload_auth, headers=headers)
            print(f"Status code: {response_auth.status_code}")
            print("Respuesta de autenticación:")
            print(json.dumps(response_auth.json(), indent=2))
            response_auth.raise_for_status()
        except Exception as e:
            print(f"❌ Error durante la autenticación: {e}")
            return f"❌ Error de autenticación: {response_auth.status_code}"

        # Verificar si la autenticación fue exitosa
        response_data = response_auth.json()
        session_token = None
        
        # Intentar encontrar el token en diferentes lugares posibles
        if "token" in response_data:
            session_token = response_data["token"]
        elif "data" in response_data and "token" in response_data["data"]:
            session_token = response_data["data"]["token"]
        elif "user" in response_data and "token" in response_data["user"]:
            session_token = response_data["user"]["token"]
        else:
            # Si no encontramos el token, buscamos cualquier campo que pueda servir como token
            print("⚠️ No se encontró la clave 'token' en la respuesta. Buscando alternativas...")
            
            possible_token_keys = ["id_token", "auth_token", "access_token", "jwt", "session_id"]
            for possible_key in possible_token_keys:
                if possible_key in response_data:
                    session_token = response_data[possible_key]
                    print(f"✅ Se utilizará '{possible_key}' como token")
                    break
            else:
                if "user" in response_data and "id" in response_data["user"]:
                    session_token = response_data["user"]["id"]
                    print(f"⚠️ No se encontró token, se utilizará el ID de usuario como token: {session_token}")
                else:
                    print("❌ No se pudo encontrar un token en la respuesta.")
                    return "❌ No se pudo encontrar un token en la respuesta"
        
        print("✅ Conexión establecida")
        
        if args.whiteboard:
            print("🔍 Obteniendo whiteboard directo con ID 244419...")
            html_content = obtener_wod_whiteboard("244419", session_token)
            if html_content:
                nombre_archivo = f"wod_244419_directo.html"
                titulo_html = f"WOD - ID: 244419 (Directo)"
                guardar_html(titulo_html, html_content, nombre_archivo)
        else:
            # Si se proporcionó un ID de WOD específico
            if args.id_wod:
                html_content = obtener_wod_whiteboard(args.id_wod, session_token)
                if html_content:
                    nombre_archivo = f"wod_{args.id_wod}.html"
                    titulo_html = f"WOD - ID: {args.id_wod}"
                    guardar_html(titulo_html, html_content, nombre_archivo)
                return "✅ WOD obtenido exitosamente"
            
            # ✅ 2. OBTENER WODS
            wods_encontrados = []
            
            # Si se especificó una fecha específica
            if args.fecha:
                try:
                    fecha = datetime.strptime(args.fecha, "%d-%m-%Y")
                    # Verificar si es fin de semana cuando no están incluidos
                    if not include_weekends and fecha.weekday() >= 5:
                        return "ℹ️ No se obtienen WODs los fines de semana cuando no están habilitados"
                    wod = obtener_wod_para_fecha(fecha, session_token, exportar_html=args.html)
                    if wod:
                        wods_encontrados.append(wod)
                except ValueError:
                    print("❌ Formato de fecha incorrecto. Usa el formato DD-MM-YYYY.")
                    return "❌ Formato de fecha incorrecto"
            
            # Si se pidió toda la semana o no se especificó ninguna opción
            elif args.semana or not args.fecha:
                lunes, viernes = obtener_rango_semana_actual()
                fecha_actual = lunes
                
                print(f"🗓️ Buscando WODs: {lunes.strftime('%d/%m/%Y')} al {viernes.strftime('%d/%m/%Y')}")
                
                # Obtener WODs para cada día de la semana
                while fecha_actual <= viernes:
                    print(f"\nBuscando WOD para {fecha_actual.strftime('%d/%m/%Y')}...")
                    wod = obtener_wod_para_fecha(fecha_actual, session_token, exportar_html=args.html)
                    if wod:
                        wods_encontrados.append(wod)
                    else:
                        print(f"No se encontró WOD para {fecha_actual.strftime('%d/%m/%Y')}")
                    fecha_actual += timedelta(days=1)
            
            # ✅ 3. MOSTRAR RESULTADOS
            if wods_encontrados:
                # Ordenar los WODs por día de la semana
                wods_encontrados.sort(key=lambda x: x["valor_orden"])
                
                print(f"\n✨ Se encontraron {len(wods_encontrados)} WODs para esta semana:")
                
                for wod in wods_encontrados:
                    print("\n" + wod["texto_completo"])
                    if wod.get("ruta_html"):
                        print(f"✅ Documento HTML: {wod['ruta_html']}")
                    print("-" * 50)
                
                # Enviar correo solo si hay WODs y no es solo mostrar
                if not args.mostrar:
                    lunes, viernes = obtener_rango_semana_actual()
                    lunes_fmt = lunes.strftime("%d/%m/%Y")
                    viernes_fmt = viernes.strftime("%d/%m/%Y")
                    if enviar_correo_con_wods(wods_encontrados, lunes_fmt, viernes_fmt):
                        return f"✅ Se encontraron {len(wods_encontrados)} WODs y se enviaron por correo correctamente"
                    else:
                        return f"⚠️ Se encontraron {len(wods_encontrados)} WODs pero hubo un error al enviar el correo"
                else:
                    return f"✅ Se encontraron {len(wods_encontrados)} WODs (solo mostrar, no se envió correo)"
            else:
                print("ℹ️ No se encontraron WODs para esta semana")
                return "ℹ️ No se encontraron WODs para esta semana. No se envió correo."
    
    except requests.exceptions.ConnectionError as e:
        if "NameResolutionError" in str(e):
            return "❌ Error: No se puede conectar al servidor. Verifica tu conexión a Internet."
        return f"❌ Error de conexión: {str(e)}"
    except Exception as e:
        return f"❌ Error inesperado: {str(e)}"

if __name__ == "__main__":
    main(include_weekends=True)
