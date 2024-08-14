import json

archivo = 'historial.json'
texto=[]
car = 0
palabras = []
total_palabras = 0


with open(archivo, 'r') as file:
    contenido=json.load(file)
    
for item in contenido:
    texto.append(item['content'])

for i in texto:
    palabras.append(i)
    for j in i:
        car+=1

for p in palabras:
    total_palabras+=len(p.split(' '))
    
  
print(f'Cantidad de conversaciones:{len(texto)//2}')
print(f'Cantidad de caracteres: {car}')
print(f'Cantidad de palabras: {total_palabras}')
