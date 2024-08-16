from cryptography.fernet import Fernet
import json
import os
import groq_apikey
from iabot import HISTORIAL_FILE



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