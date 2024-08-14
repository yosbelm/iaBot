# Bot de Telegram: IA Conversacional con Llama 3.1

Este es un bot de Telegram que utiliza un modelo de IA conversacional basado en Llama 3.1 (70B). El bot puede recibir documentos PDF, extraer el contexto y almacenar la información en un archivo `historial.json`.

## Requisitos

Antes de ejecutar el bot, asegúrate de tener instalado Python y los siguientes requisitos:

1. **Python 3.x** (recomendado: 3.8 o superior)
2. **Pip** (gestor de paquetes de Python)

## Instalación

1. Clona este repositorio o descarga los archivos.

    ```bash
    git clone https://github.com/yosbelm/iaBot.git
    cd iaBot
    ```

2. Crea los archivos necesarios para la configuración:  
   `groq_apikey`: Este archivo debe contener tu API key de Groq.  
   `telegram_token`: Este archivo debe contener el token de tu bot de Telegram.  

3. Crea una carpeta llamada `downloads` donde se almacenarán los PDF que se suban. Por defecto, los archivos se borrarán después de procesarlos.

    ```bash
    mkdir downloads
    ```

4. Instala las dependencias necesarias:

    ```bash
    pip install -r requirements.txt
    ```

5. Asegúrate de que tu bot de Telegram esté configurado correctamente y que tengas los permisos necesarios.

6. Ejecuta el bot:

    ```bash
    python iabot.py
    ```

El bot estará listo para recibir mensajes y procesarlos. Envía un documento PDF al bot y comienza la conversación. El contexto del PDF se almacenará en `historial.json`.

## Estadísticas de Uso

El bot incluye un archivo llamado `stats.py` que sirve para ver las estadísticas de uso de la IA. Estas estadísticas incluyen la cantidad de conversaciones, palabras y caracteres procesados. Para ejecutar `stats.py` y ver las estadísticas, usa el siguiente comando:

```bash
python stats.py
