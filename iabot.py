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


TOKEN = telegram_token.api_token
client = Groq(api_key=groq_apikey.api_key)
HISTORIAL_FILE = 'historial.json'
PDF_FILES = ['']
bot_active = False  # Estado global del bot


async def handle_text(update: Update, context: CallbackContext) -> None:
    if bot_active:
        user_input = update.message.text
        contexto_pdf = cargar_historial()
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
        
        
        
def cargar_historial():
    try:
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return [{"role": "system", "content": groq_apikey.contexto}]


def guardar_historial(historial):
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as file:
        json.dump(historial, file, ensure_ascii=False, indent=4)


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
        contexto_pdf = cargar_historial()
        response = obtener_respuesta(user_input, contexto_pdf)
        await update.message.reply_text(response)
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')


async def handle_pdf(update: Update, context: CallbackContext) -> None:
    if bot_active:
        file = await update.message.document.get_file()
        file_path = f'downloads/{file.file_id}.pdf'

        # Descarga el archivo PDF
        await file.download_to_drive(file_path)

        pdf_text = ''
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    pdf_text += page.extract_text() or ''

            history = cargar_historial()
            history.append({"role": "system", "content": pdf_text})
            guardar_historial(history)

            await update.message.reply_text('Contenido PDF almacenado. Contexto para AI disponible.')
        except Exception as e:
            logging.error(f"Error al procesar el PDF: {e}")
            await update.message.reply_text('No se pudo procesar el PDF.')

        os.remove(file_path)  # Eliminar el archivo PDF de la carpeta downloads
    else:
        await update.message.reply_text('El bot está detenido. Usa /start para iniciarlo.')


def obtener_respuesta(prompt, historial):
    historial.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=historial,
        model="llama-3.1-8b-instant",
        temperature=0.5,
        max_tokens=1024,
    )

    respuesta = chat_completion.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})
    guardar_historial(historial)
    return respuesta


async def exit_bot(update: Update, context: CallbackContext) -> None:
    global bot_active
    bot_active = False
    await update.message.reply_text('El bot se ha detenido. Usa /start para iniciarlo nuevamente.')


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))
    app.add_handler(CommandHandler("exit", exit_bot))

    app.run_polling()

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    main()