# WOD Scraper App

Una aplicación Android para obtener automáticamente los WODs (Workout of the Day) de CrossFit DB y Box N8.

## Características

- Obtiene los WODs del día actual
- Interfaz moderna con Material Design 3
- Soporte para múltiples gimnasios
- Envío automático de WODs por correo
- Diseño responsive y amigable

## Requisitos

- Android Studio Hedgehog | 2023.1.1
- Android SDK 33+
- Python 3.10
- Chaquopy (Python SDK para Android)

## Configuración

1. Clona el repositorio:
```bash
git clone https://github.com/FeloSP8/wod-scraper-app.git
```

2. Copia el archivo `config.example.py` a `config.py` y configura tus credenciales

3. Abre el proyecto en Android Studio y sincroniza con Gradle

## Dependencias

- androidx.compose:compose-bom:2024.02.00
- androidx.compose.material3:material3
- com.chaquo.python:python
- requests (Python)
- beautifulsoup4 (Python)

## Licencia

MIT License