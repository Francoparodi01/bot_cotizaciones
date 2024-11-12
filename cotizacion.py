import requests
import telebot
import os
import certifi
from dotenv import load_dotenv
from datetime import datetime, timedelta
import matplotlib
import schedule
import time
import threading
import io
import matplotlib.pyplot as plt
import pandas as pd


# Cargamos las variables desde el archivo .env
load_dotenv()

# Variables obtenidas desde el .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BCRA_TOKEN = os.getenv('API_BCRA_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Inicializamos el bot con telebot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Variables globales 
ultimo_precio_oficial = None
ultimo_precio_blue = None

# Funciones para obtener datos

def fetch_data(url, headers=None):
    try:
        response = requests.get(url, verify=False, headers=headers)
        response.raise_for_status()  # Lanza un error si la respuesta no es 200
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ocurrió un error: {str(e)}")
        return None

# Funciones específicas de la API

def get_usd_of():
    data = fetch_data('https://dolarapi.com/v1/ambito/dolares/oficial')
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible') if data else (None, None)

def get_usd_blue():
    data = fetch_data('https://dolarapi.com/v1/ambito/dolares/blue')
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible') if data else (None, None)

def get_usd_card():
    data = fetch_data('https://dolarapi.com/v1/ambito/dolares/tarjeta')
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible') if data else (None, None)

def get_reservas_internacionales():
    fechaHoy = datetime.now().strftime('%Y-%m-%d')
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/1/2023-12-10/{fechaHoy}'
    data = fetch_data(url)
    return [(item['fecha'], item['valor']) for item in data['results']] if data and 'results' in data else []

# Funciones para obtener la inflación
def get_inflation_data():
    fecha_inicio = '2023-12-10'
    fecha_hoy_str = datetime.now().strftime('%Y-%m-%d')

    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/27/{fecha_inicio}/{fecha_hoy_str}'

    data = fetch_data(url)
    
    if data and 'results' in data:
        return [(item['fecha'], item['valor']) for item in data['results']]
    
    return []

def get_base_monetaria():
    fechaHoy = datetime.now().strftime('%Y-%m-%d')
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/16/2023-12-10/{fechaHoy}'
    data = fetch_data(url)
    return [(item['fecha'], item['valor']) for item in data['results']] if data and 'results' in data else []

def get_base_monetaria_ampliada():
    fechaHoy = datetime.now().strftime('%Y-%m-%d')
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/17/2023-12-10/{fechaHoy}'
    data = fetch_data(url)
    return [(item['fecha'], item['valor']) for item in data['results']] if data and 'results' in data else []

def get_historical_data(start_date, end_date):
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/27/{start_date}/{end_date}'
    data = fetch_data(url)
    return [(item['fecha'], item['valor']) for item in data['results']] if data and 'results' in data else []

def get_politica_monetaria():
    fechaHoy = datetime.now().strftime('%Y-%m-%d')
    url = f'https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/34/2023-12-10/{fechaHoy}'
    data = fetch_data(url)
    return [(item['fecha'], item['valor']) for item in data['results']] if data and 'results' in data else []


# ---------------------------------------------------------------------------------------------------------------
# Gráficos 

def plot_reservas(data):
    if data:
        fechas, valores = zip(*data)  # Descomponemos en dos listas, fechas y valores
        fechas = [datetime.strptime(fecha, '%Y-%m-%d').date() for fecha in fechas]  # Convertimos fechas a formato datetime
        
        plt.figure(figsize=(14, 8))
        plt.fill_between(fechas, valores, color="skyblue", alpha=0.4)  # Gráfico de área
        plt.plot(fechas, valores, color="Slateblue", alpha=0.6, linewidth=2)  # Línea con marcadores
        
        plt.title('Reservas Internacionales del BCRA', fontsize=14)
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Valor (en millones)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.ylim(bottom=20000) 

        # Guardar la imagen en un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf  # Devolver el buffer con la imagen
    else:
        return None

def plot_base_monetaria(data_base_monetaria):
    if data_base_monetaria:
        fechas, valores = zip(*data_base_monetaria)
        fechas = [datetime.strptime(fecha, '%Y-%m-%d').date() for fecha in fechas]

        plt.figure(figsize=(14, 8))
        plt.fill_between(fechas, valores, color="skyblue", alpha=0.4, label='Base Monetaria')
        plt.plot(fechas, valores, color="Slateblue", alpha=0.6, linewidth=2)
        
        plt.title('Base Monetaria', fontsize=14)
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Valor (en millones)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.legend()

        # Guardar la imagen en un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf  # Devolver el buffer con la imagen
    else:
        print("La base monetaria está vacía.")
        return None

#grafico de la inflacion

def plot_inflation(data):
    if data:
        fechas, valores = zip(*data)  # Descomponemos en dos listas, fechas y valores
        fechas = [datetime.strptime(fecha, '%Y-%m-%d').date() for fecha in fechas]  # Convertimos fechas a formato datetime
        
        plt.figure(figsize=(14, 8))
        plt.plot(fechas, valores, marker='o', color='red', linewidth=2)  # Gráfico de línea
        
        plt.title('Inflación desde el 10 de diciembre de 2023', fontsize=14)
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Inflación (%)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()

        # Guardar la imagen en un buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf  # Devolver el buffer con la imagen
    else:
        print("No hay datos para graficar.")
        return None

# Comandos del bot telegram
# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy tu bot económico. Puedes consultar:\n - /dolar_oficial\n - /dolar_blue\n - /dolar_tarjeta\n - /tasa_leliq\n - /base_monetaria\n - /graficar_base")

# Comando /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "¡Hola! Soy tu bot económico. Puedes consultar:\n"
        " - /dolar_oficial: Precio del dólar oficial.\n"
        " - /dolar_blue: Precio del dólar blue.\n"
        " - /dolar_tarjeta: Precio del dólar tarjeta.\n"
        " - /base_monetaria: Datos de la base monetaria.\n"
        " - /inflacion: Últimos datos de inflación.\n"
        " - /graficar_reservas: Gráfico de reservas internacionales.\n"
        " - /graficar_inflacion: Gráfico de la inflación.\n"
        " - /graficar_base: Gráfico de la base monetaria.\n"
    )
    bot.reply_to(message, help_text)

# Comando para obtener el dólar oficial
@bot.message_handler(commands=['dolar_oficial'])
def dolar_oficial(message):
    compra, venta = get_usd_of()
    if compra and venta:
        bot.reply_to(message, f"Dólar oficial - Compra: {compra} ARS, Venta: {venta} ARS")
    else: 
        bot.reply_to(message, "No se pudo obtener el tipo de cambio oficial.")

# Comando para obtener el dólar blue
@bot.message_handler(commands=['dolar_blue'])
def dolar_blue(message):
    compra, venta = get_usd_blue()
    if compra and venta:
        bot.reply_to(message, f"Dólar Blue - Compra: {compra} ARS, Venta: {venta} ARS")
    else:
        bot.reply_to(message, "No se pudo obtener el tipo de cambio blue.")

# Comando para obtener el dólar tarjeta
@bot.message_handler(commands=['dolar_tarjeta'])
def dolar_tarjeta(message):
    compra, venta = get_usd_card()
    if compra and venta:
        bot.reply_to(message, f"Dólar Tarjeta - Compra: {compra} ARS, Venta: {venta} ARS")
    else:
        bot.reply_to(message, "No se pudo obtener el tipo de cambio del dólar tarjeta.")

# Comando para obtener la base monetaria
@bot.message_handler(commands=['base_monetaria'])
def base_monetaria(message):
    base = get_base_monetaria()
    bot.reply_to(message, f"La base monetaria es: {base}")

# comando para obtener la inflación

@bot.message_handler(commands=['inflacion'])
def inflacion(message):
    inflacion_data = get_inflation_data()
    if inflacion_data:
        inflacion_str = "\n".join([f"{fecha}: {valor}%" for fecha, valor in inflacion_data])
        bot.reply_to(message, f"Datos de Inflación:\n{inflacion_str}")
    else:
        bot.reply_to(message, "No se pudo obtener datos de inflación.")

# grafico de las reservas internacionales
@bot.message_handler(commands=['graficar_reservas'])
def graficar_reservas(message):
    data = get_reservas_internacionales()  # Obtener los datos de reservas internacionales
    img_buffer = plot_reservas(data)  # Generar el gráfico y guardar en un buffer
    if img_buffer:
        bot.send_photo(message.chat.id, img_buffer)  # Enviar el gráfico al usuario
    else:
        bot.reply_to(message, "No se pudieron graficar las reservas internacionales.")

# Comando para graficar la base monetaria
@bot.message_handler(commands=['graficar_base'])
def graficar_base_monetaria(message):
    data_base_monetaria = get_base_monetaria()  # Obtener los datos de la base monetaria
    img_buffer = plot_base_monetaria(data_base_monetaria)  # Generar el gráfico y guardar en un buffer
    if img_buffer:
        bot.send_photo(message.chat.id, img_buffer)  # Enviar el gráfico al usuario
    else:
        bot.reply_to(message, "No se pudo graficar la base monetaria.")

# Comando para graficar la inflación
@bot.message_handler(commands=['graficar_inflacion'])
def graficar_inflacion(message):
    data_inflation = get_inflation_data()  # Obtener los datos de inflación
    img_buffer = plot_inflation(data_inflation)  # Generar el gráfico y guardar en un buffer
    if img_buffer:
        bot.send_photo(message.chat.id, img_buffer)  # Enviar el gráfico al usuario
    else:
        bot.reply_to(message, "No se pudo graficar la inflación.")


# Si el bot recibe un mensaje no reconocido
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "¡No entiendo lo que quieres decirme! Usa los comandos /start o /help para obtener más información.")

# Main
if __name__ == "__main__":
    bot.polling(none_stop=True)