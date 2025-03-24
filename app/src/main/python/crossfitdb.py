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

# ... resto del contenido del archivo crossfitdb.py ...