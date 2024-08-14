# Bot de Telegram: IA Conversacional con Llama 3.1

Este es un bot de Telegram que utiliza un modelo de IA conversacional basado en Llama (llama-3.1-70b-versatile por defecto). El bot puede recibir documentos PDF, extraer el contexto y almacenar la información en un archivo `historial.json`.

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
   `groq_apikey`: Este archivo debe contener tu API key de Groq y una variable `contexto` con un string que incluya la información que se le va a dar a la IA, como la personalidad y cómo debe responder. Ejemplo de contenido del archivo `groq_apikey`:
   
   ```plaintext
   api_key="tu_api_key_de_groq"
   contexto="Información que define la personalidad y la respuesta de la IA."  
   ```
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
```

## Configuración del Modelo

Se puede cambiar el modelo de Llama cambiando el valor del parámetro `model`. Los modelos disponibles son:

- `"llama-3.1-70b-versatile"`
- `"llama-3.1-8b-instant"`
- `"llama3-groq-70b-8192-tool-use-preview"`
- `"llama3-groq-8b-8192-tool-use-preview"`
- `"llama-guard-3-8b"`

Los modelos más avanzados son los de la versión 3.1. Además, se puede configurar la temperatura entre los valores 0 y 2 en el parámetro `temperature`, donde valores más bajos hacen que las respuestas sean más ajustadas a lo que se le pide. Consulta la documentación en esta página para más detalles: [Groq API Reference](https://console.groq.com/docs/api-reference#chat).
