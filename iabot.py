import os
from groq import Groq
import PyPDF2
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext, CommandHandler
import httpx
import telegram_token
import groq_apikey
from encript import *



TOKEN = telegram_token.api_token
client = Groq(api_key=groq_apikey.api_key)
HISTORIAL_FILE = 'historial.json'
bot_active = False

        
        
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