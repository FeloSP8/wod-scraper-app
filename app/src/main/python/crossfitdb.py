import requests
import json
from datetime import datetime, timedelta
from config import CROSSFITDB_CONFIG

def get_auth_token():
    url = "https://crossfitdb.com.br/api/v1/auth/login"
    payload = {
        "username": CROSSFITDB_CONFIG["username"],
        "password": CROSSFITDB_CONFIG["password"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["token"]
    except Exception as e:
        return f"Error al obtener token: {str(e)}"

def get_wod(token, date_str):
    url = "https://crossfitdb.com.br/api/v1/wod/list"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "id_user": CROSSFITDB_CONFIG["id_user"],
        "id_application": CROSSFITDB_CONFIG["id_application"],
        "date": date_str
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return f"Error al obtener WOD: {str(e)}"

def format_wod(wod_data):
    if not wod_data or not isinstance(wod_data, list) or len(wod_data) == 0:
        return "No hay WOD disponible para esta fecha"
    
    wod = wod_data[0]
    formatted = f"📅 {wod.get('date', 'Fecha no disponible')}\n"
    formatted += "=" * 30 + "\n"
    
    if wod.get('warmup'):
        formatted += "🔥 WARMUP:\n"
        formatted += f"{wod['warmup']}\n\n"
    
    if wod.get('skill'):
        formatted += "🎯 SKILL:\n"
        formatted += f"{wod['skill']}\n\n"
    
    if wod.get('wod'):
        formatted += "💪 WOD:\n"
        formatted += f"{wod['wod']}\n"
    
    return formatted

def main(semana=False, include_weekends=False):
    try:
        token = get_auth_token()
        if isinstance(token, str) and token.startswith("Error"):
            return token
        
        result = "📱 CrossFitDB\n"
        result += "=" * 30 + "\n\n"
        
        if semana:
            # Obtener WODs para la semana
            today = datetime.now()
            for i in range(7):
                date = today + timedelta(days=i)
                # Saltar fines de semana si no están incluidos
                if not include_weekends and date.weekday() >= 5:
                    continue
                date_str = date.strftime("%Y-%m-%d")
                wod_data = get_wod(token, date_str)
                if isinstance(wod_data, str) and wod_data.startswith("Error"):
                    result += f"{wod_data}\n"
                else:
                    result += format_wod(wod_data) + "\n\n"
        else:
            # Solo obtener WOD de hoy
            today = datetime.now().strftime("%Y-%m-%d")
            wod_data = get_wod(token, today)
            if isinstance(wod_data, str) and wod_data.startswith("Error"):
                result += wod_data
            else:
                result += format_wod(wod_data)
        
        return result
    
    except Exception as e:
        return f"Error inesperado: {str(e)}"

if __name__ == "__main__":
    print(main())