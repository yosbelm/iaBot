import json
import os
import logging
import PyPDF2
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler
import telegram_token
from groq import Groq
import groq_apikey
import httpx
from cryptography.fernet import Fernet




TOKEN = telegram_token.api_token
client = Groq(api_key=groq_apikey.api_key)
HISTORIAL_FILE = 'historial.json'
bot_active = False

        
        

# Cargar o generar la clave
def load_or_generate_key(key_filename):
    if os.path.exists(key_filename):
        with open(key_filename, 'rb') as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(key_filename, 'wb') as key_file:
            key_file.write(key)
        return key

key_filename = 'secret.key'
key = load_or_generate_key(key_filename)
cipher_suite = Fernet(key)    
      
# Encriptar y guardar el archivo JSON    
def save_encrypted_json(filename, data, cipher_suite):
    json_data = json.dumps(data).encode()
    encrypted_data = cipher_suite.encrypt(json_data)
    with open(filename, 'wb') as file:
        file.write(encrypted_data)

# Leer y desencriptar el archivo JSON, si el archivo está vacío crea la información con el contexto dado
def load_encrypted_json(filename, cipher_suite):
    nuevo_contexto = [{"role": "system", "content": groq_apikey.contexto}]
    try:
        with open(filename, 'rb') as file:
            encrypted_data = file.read()
            if encrypted_data == b'':
                return json.load(save_encrypted_json(HISTORIAL_FILE, nuevo_contexto, cipher_suite))
            else:
                decrypted_data = cipher_suite.decrypt(encrypted_data)
                return json.loads(decrypted_data)
    except:
        with open(filename, 'rb') as file:
            encrypted_data = file.read()
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        



async def start(update: Update, context: CallbackContext) -> None:
    global bot_active
    if not bot_active:
        bot_active = True
        await update.message.reply_text('¡Hola! Soy un bot conversacional que utiliza el modelo de lenguaje LLaMA 3.1 para responder a tus preguntas y conversaciones 🤖. Puedes proporcionarme contexto enviándome archivos PDF 📁 para que pueda entender mejor tus necesidades 🤔. ¡Empecemos!')
    else:
        await update.message.reply_text('El bot ya está en funcionamiento.')


async def handle_text(update: Update, context: CallbackContext) -> None:
    if bot_active:
        user_input = update.message.text
        contexto_pdf = load_encrypted_json(HISTORIAL_FILE, cipher_suite)
        try:
            response = obtener_respuesta(user_input, contexto_pdf)
            await update.message.reply_text(response)
        except httpx.ConnectTimeout:
            await update.message.reply_text('Error de conexión. Intenta de nuevo más tarde.')
        except Exception as e:
            logging.error(f"Ocurrió un error: {e}")
            await update.message.reply_text('Ocurrió un error inesperado. Intenta de nuevo.')
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')


async def handle_pdf(update: Update, context: CallbackContext) -> None:
    if bot_active:
        file = await update.message.document.get_file()
        file_path = f'downloads/{file.file_id}.pdf'
        await file.download_to_drive(file_path)   # Descarga el archivo PDF

        pdf_text = ''
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    pdf_text += page.extract_text() or ''

            history = load_encrypted_json(HISTORIAL_FILE, cipher_suite)
            history.append({"role": "system", "content": pdf_text})
            save_encrypted_json(HISTORIAL_FILE, history, cipher_suite)

            await update.message.reply_text('Contenido PDF almacenado. Contexto para AI disponible.')
        except Exception as e:
            logging.error(f"Error al procesar el PDF: {e}")
            await update.message.reply_text('No se pudo procesar el PDF.')

        os.remove(file_path)  # Eliminar el archivo PDF de la carpeta 'downloads', por defecto se elimina
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')


async def handle_audio(update: Update, context: CallbackContext) -> None:
    if bot_active:
        audio_file = await update.message.voice.get_file()
        file_path = os.path.join('audio', f'{audio_file.file_id}.ogg')
        await audio_file.download_to_drive(file_path)   # Descarga el audio
        try:
            # Lee el contenido del archivo de audio
            with open(file_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(file_path, file.read()),
                    model="whisper-large-v3",
                    prompt="Transcribe el audio de manera literal y precisa, sin interpretaciones ni conjeturas. Respetar las reglas de gramática, ortografía y sintaxis del idioma. No omitir ni agregar información. Si hay errores de pronunciación o entonación, transcribir exactamente lo que se escucha. No hacer suposiciones ni inferencias. Transcripción debe ser fiel y exacta al contenido del audio.",
                    response_format="json",
                    language="es",
                    temperature=0.0
                )
                respuesta = transcription.text
                # Guarda la respuesta en el historial
                historial = load_encrypted_json(HISTORIAL_FILE, cipher_suite)
                historial.append({"role": "assistant", "content": respuesta})
                save_encrypted_json(HISTORIAL_FILE, historial, cipher_suite)
                # Envía la transcripción al usuario
                await update.message.reply_text(respuesta)
        
        except Exception as e:
            logging.error(f"Error al procesar el audio: {e}")
            await update.message.reply_text('No se pudo procesar el audio.')
        
        os.remove(file_path)    # Eliminar el archivo de audio de la carpeta 'audio', por defecto se elimina
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')   
    
    
    
def obtener_respuesta(prompt, historial):
    # Desencripta el archivo json para poder ser dado al contexto y lo carga como lista para poder usar append
    historial = list(load_encrypted_json(HISTORIAL_FILE, cipher_suite))
    # Agrega al historial el texto introducido por el usuario
    historial.append({"role": "user", "content": prompt})
    chat_completion = client.chat.completions.create(
        messages=historial,
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024,
    )
    respuesta = chat_completion.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})
    save_encrypted_json(HISTORIAL_FILE, historial, cipher_suite)
    return respuesta


async def exit_bot(update: Update, context: CallbackContext) -> None:
    global bot_active
    bot_active = False
    await update.message.reply_text('El bot se ha detenido. Usa /start para iniciarlo.')
 
    
async def clear_context(update: Update, context: CallbackContext) -> None:
    if bot_active:
        try:
            with open(HISTORIAL_FILE, 'w', encoding='utf-8') as file:
                file.write('')
        finally:
            await update.message.reply_text('Contexto reiniciado.')
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))
    app.add_handler(MessageHandler(filters.VOICE, handle_audio))
    app.add_handler(CommandHandler("clear_context", clear_context))
    app.add_handler(CommandHandler("exit", exit_bot))
    
    app.run_polling()

if __name__ == '__main__':
    # Crea la carpeta downloads si no existe
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    # Crea la carpeta downloads si no existe
    os.makedirs('audio', exist_ok=True)
    # Crea la base de datos json si no existe
    if not os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'w', encoding='utf-8') as file:
            pass
    main()