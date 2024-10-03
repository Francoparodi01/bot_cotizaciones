import requests
import telebot
import os
from dotenv import load_dotenv

# Cargamos las variables desde el archivo .env
load_dotenv()

# Variables obtenidas desde el .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_BCRA_TOKEN = os.getenv('API_BCRA_TOKEN')

# Inicializamos el bot con telebot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Función para obtener el tipo de cambio del dólar oficial
def get_usd_of():
    url = 'https://dolarapi.com/v1/dolares/oficial'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        compra = data.get('compra', 'No disponible')
        venta = data.get('venta', 'No disponible')
        return compra, venta
    else:
        return "No se pudo obtener el tipo de cambio oficial."

# Función para obtener el tipo de cambio blue (con compra y venta)
def get_usd_blue():
    url = 'https://dolarapi.com/v1/dolares/blue'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        compra = data.get('compra', 'No disponible')
        venta = data.get('venta', 'No disponible')
        return compra, venta
    else:
        return None, None

# Función para obtener la tasa Leliq
def get_leliq_rate():
    API_BCRA_TOKEN = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTk0MjkzNzYsInR5cGUiOiJleHRlcm5hbCIsInVzZXIiOiJmcmFuY29wYXJvZGkyMDAxQGdtYWlsLmNvbSJ9.nBLKI1-QFo8CmNu12odtAU5YrojI_13d2ylzmQtOT539Ot85xwJJouE8DeOAeZnJ_4WH_i6t0dBKvH_AoDl9tA'
    HEADERS = {'Authorization': f'BEARER {API_BCRA_TOKEN}'}
    url = 'https://api.estadisticasbcra.com/leliq'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data[-1]['v']  # Última tasa Leliq
    else:
        return "No se pudo obtener la tasa de Leliq."

# Función para obtener el tipo de cambio del dólar tarjeta
def get_usd_card():
    url = 'https://dolarapi.com/v1/dolares/tarjeta'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        compra = data.get('compra', 'No disponible')
        venta = data.get('venta', 'No disponible')
        return compra, venta
    else:
        return "No se pudo obtener el tipo de cambio del dólar tarjeta."

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Soy tu bot económico. Puedes consultar:\n - /dolar_oficial\n - /dolar_blue\n - /dolar_tarjeta\n - /tasa_leliq")

# Comando /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "¡Hola! Soy tu bot económico. Puedes consultar:\n - /dolar_oficial\n - /dolar_blue\n - /tasa_leliq")

# Comando para obtener el dólar oficial
@bot.message_handler(commands=['dolar_oficial'])
def dolar_oficial(message):
    compra, venta = get_usd_of()
    if compra and venta:
        bot.reply_to(message, f"Dólar oficial - Compra: {compra} ARS, Venta: {venta} ARS")
    else: 
        bot.reply_to(message, "No se pudo obtener el tipo de cambio oficial.")

# Comando para obtener el dólar blue (compra y venta)
@bot.message_handler(commands=['dolar_blue'])
def dolar_blue(message):
    compra, venta = get_usd_blue()
    if compra and venta:
        bot.reply_to(message, f"Dólar Blue - Compra: {compra} ARS, Venta: {venta} ARS")
    else:
        bot.reply_to(message, "No se pudo obtener el tipo de cambio blue.")

# Comando para obtener la tasa Leliq
@bot.message_handler(commands=['tasa_leliq'])
def tasa_leliq(message):
    leliq = get_leliq_rate()
    bot.reply_to(message, f"La tasa de interés Leliq es: {leliq}%")

# Comando para obtener el dólar tarjeta
@bot.message_handler(commands=['dolar_tarjeta'])
def dolar_tarjeta(message):
    compra, venta = get_usd_card()
    if compra and venta:
        bot.reply_to(message, f"Dólar Tarjeta - Compra: {compra} ARS, Venta: {venta} ARS")
    else:
        bot.reply_to(message, "No se pudo obtener el tipo de cambio del dólar tarjeta.")

# Si el bot recibe un mensaje no reconocido
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "¡No entiendo lo que quieres decirme! Por favor, utiliza los comandos /start o /help para obtener más información.")

# Inicializar el bot
if __name__ == "__main__":
    bot.polling(none_stop=True)
