import json
import os
import logging
import PyPDF2
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext
import telegram_token
from groq_apikey import Groq
import groq_apikey



TOKEN = telegram_token.api_token
client = Groq(api_key=groq_apikey.api_key)
HISTORIAL_FILE = 'historial.json'
PDF_FILES = ['']


def cargar_historial():
    try:
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return [{"role": "system", "content": groq_apikey.contexto}]


def guardar_historial(historial):
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as file:
        json.dump(historial, file, ensure_ascii=False, indent=4)


async def handle_text(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    contexto_pdf = cargar_historial()  # Obtiene el contexto del historial
    response = obtener_respuesta(user_input, contexto_pdf)
    
    await update.message.reply_text(response)


async def handle_pdf(update: Update, context: CallbackContext) -> None:
    file = await update.message.document.get_file()
    file_path = f'downloads/{file.file_id}.pdf'
    
    # Descarga el archivo PDF
    await file.download_to_drive(file_path)

    # Convierte el PDF a texto y lo agrega al historial
    pdf_text = ''
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                pdf_text += page.extract_text() or ''
        
        # Cargar el historial y agregar el contenido del PDF
        history = cargar_historial()
        history.append({"role": "system", "content": pdf_text})
        guardar_historial(history)

        await update.message.reply_text('El contenido del PDF ha sido guardado en el historial.')
    except Exception as e:
        logging.error(f"Error al procesar el PDF: {e}")
        await update.message.reply_text('No se pudo procesar el PDF.')

    # Limpia archivos descargados (opcional)
    os.remove(file_path)


def obtener_respuesta(prompt, historial):
    historial.append({"role": "user", "content": prompt})
    
    chat_completion = client.chat.completions.create(
        messages=historial,
        model="llama-3.1-70b-versatile", 
        temperature=0.5,
        max_tokens=1024,
    )
    
    respuesta = chat_completion.choices[0].message.content
    historial.append({"role": "assistant", "content": respuesta})
    guardar_historial(historial)
    return respuesta



def main() -> None:
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf))
    
    app.run_polling()

if __name__ == '__main__':
    main()