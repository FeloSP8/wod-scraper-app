import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from config import EMAIL_CONFIG

# ... resto del contenido del archivo n8.py ...