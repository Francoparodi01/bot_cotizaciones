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
    data = fetch_data('https://dolarapi.com/v1/dolares/oficial')
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible') if data else (None, None)

def get_usd_blue():
    data = fetch_data('https://dolarapi.com/v1/dolares/blue')
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible') if data else (None, None)

def get_usd_card():
    data = fetch_data('https://dolarapi.com/v1/dolares/tarjeta')
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

def get_usd_of():
    data = requests.get('https://dolarapi.com/v1/dolares/oficial').json()
    return data.get('compra', 'No disponible'), data.get('venta', 'No disponible')

# Función para establecer el valor del dólar al inicio del día
def obtener_valor_inicial():
    global valor_usd_inicio
    compra, _ = get_usd_of()
    valor_usd_inicio = float(compra) if compra != 'No disponible' else None

# Función para comparar y mostrar la variación del dólar
def comparar_dolar():
    global valor_usd_inicio
    compra_actual, _ = get_usd_of()
    
    if compra_actual != 'No disponible' and valor_usd_inicio:
        compra_actual = float(compra_actual)
        variacion = round((compra_actual - valor_usd_inicio) / valor_usd_inicio * 100, 2)
        mensaje = f"El valor del dólar oficial ha variado un {variacion}% desde el inicio del día. Precio actual: {compra_actual}"
    else:
        mensaje = "No se pudo obtener el valor del dólar oficial actual."
    
    bot.send_message(TELEGRAM_CHAT_ID, mensaje)

# Función para configurar las alertas
def iniciar_alertas():
    obtener_valor_inicial()  # Establece el valor al inicio del día
    schedule.every().hour.do(comparar_dolar)  # Configura la alerta cada hora

    while True:
        schedule.run_pending()
        time.sleep(1)

def obtener_datos_diarios(fecha=None):
    if fecha is None:
        fecha = datetime.now().strftime('%Y-%m-%d')
    
    valor_usd_minorista = get_usd_of()
    valor_usd_mayorista = get_usd_blue()
    reservas_internacionales = get_reservas_internacionales()
    tasa_politica_monetaria = get_politica_monetaria()
    
    # Aquí asumimos que get_usd_of() y get_usd_blue() devuelven tuplas
    # Si devuelven un valor diferente, ajusta según tu lógica.
    valor_usd_minorista_variacion = valor_usd_minorista[0]  # Ajusta si es necesario
    valor_usd_mayorista_variacion = valor_usd_mayorista[0]  # Ajusta si es necesario

    datos = {
        "Tipo de Cambio Minorista": valor_usd_minorista_variacion,  
        "Tipo de Cambio Mayorista": valor_usd_mayorista_variacion,  
        "Reservas Internacionales del BCRA": reservas_internacionales,  
        "Tasa de Política Monetaria": tasa_politica_monetaria  
    }
    return datos

def calcular_variaciones(datos_hoy, datos_ayer):
    variaciones = {}
    for clave, valor_hoy in datos_hoy.items():
        valor_ayer = datos_ayer.get(clave)
        
        if valor_ayer is not None:
            # Asegúrate de que valor_hoy y valor_ayer sean números, no tuplas
            if isinstance(valor_hoy, tuple):
                valor_hoy = valor_hoy[0]  # Cambia esto según tu lógica
            if isinstance(valor_ayer, tuple):
                valor_ayer = valor_ayer[0]  # Cambia esto según tu lógica

            # Asegúrate de que los valores sean números antes de realizar la operación
            if isinstance(valor_hoy, (int, float)) and isinstance(valor_ayer, (int, float)):
                variaciones[clave] = round((valor_hoy - valor_ayer) / valor_ayer * 100, 2)
            else:
                print(f"Error: valores no numéricos para {clave} - hoy: {valor_hoy}, ayer: {valor_ayer}")

    return variaciones

def resumen_diario():
    fecha_hoy = datetime.now().strftime('%Y-%m-%d')
    fecha_ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    datos_hoy = obtener_datos_diarios()
    datos_ayer = obtener_datos_diarios(fecha_ayer)
    
    variaciones = calcular_variaciones(datos_hoy, datos_ayer)
    
    # Agrega el resumen aquí
    resumen = {
        "Resumen de variaciones": {
            "Tipo de Cambio Minorista": variaciones.get("Tipo de Cambio Minorista", 0.0),
            "Tipo de Cambio Mayorista": variaciones.get("Tipo de Cambio Mayorista", 0.0),
            "Reservas Internacionales": variaciones.get("Reservas Internacionales del BCRA", 0.0),
            "Tasa de Política Monetaria": variaciones.get("Tasa de Política Monetaria", 0.0),
        }
    }
    
    return resumen



# Funciones para gráficos 

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
    data = get_reservas_internacionales() 
    img_buffer = plot_reservas(data)  
    if img_buffer:
        bot.send_photo(message.chat.id, img_buffer)  
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
    data_inflation = get_inflation_data() 
    img_buffer = plot_inflation(data_inflation)
    if img_buffer:
        bot.send_photo(message.chat.id, img_buffer) 
    else:
        bot.reply_to(message, "No se pudo graficar la inflación.")

        
@bot.message_handler(commands=['resumen'])
def resumen(message):
    # Obtener el resumen diario
    resumen_diario_data = resumen_diario()

    # Crear un mensaje con el resumen de variaciones
    resumen_texto = "Resumen de variaciones:\n"
    for clave, valor in resumen_diario_data["Resumen de variaciones"].items():
        resumen_texto += f"{clave}: {valor}%\n"

    # Enviar el resumen al chat
    bot.reply_to(message, resumen_texto)


@bot.message_handler(commands=['dl_diario'])
def send_welcome(message):
    TELEGRAM_CHAT_ID = '8020614355'
    TELEGRAM_CHAT_ID = message.chat.id  
    dolar_oficial = get_usd_of()
    dolar_blue = get_usd_blue()
    bot.reply_to(message, f"¡Bienvenido! Las alertas del dólar oficial comenzarán cada hora.\n"
                      f"El valor del dólar oficial es: {dolar_oficial[0]}\n"
                      f"El valor del dólar blue es: {dolar_blue[0]}")

    hilo_alertas = threading.Thread(target=iniciar_alertas)
    hilo_alertas.start()

def obtener_valor_inicial():
    global valor_usd_inicio
    compra, _ = get_usd_of()
    valor_usd_inicio = float(compra) if compra != 'No disponible' else None

# Función para comparar y mostrar la variación del dólar
def comparar_dolar():
    global valor_usd_inicio
    compra_actual, _ = get_usd_of()
    
    if compra_actual != 'No disponible' and valor_usd_inicio:
        compra_actual = float(compra_actual)
        variacion = round((compra_actual - valor_usd_inicio) / valor_usd_inicio * 100, 2)
        mensaje = f"El valor del dólar oficial ha variado un {variacion}% desde el inicio del día. Precio actual: {compra_actual}"
    else:
        mensaje = "No se pudo obtener el valor del dólar oficial actual."
    
    # Enviar el mensaje automáticamente
    bot.send_message(TELEGRAM_CHAT_ID, mensaje)

# Función para enviar un resumen diario
def enviar_resumen_diario():
    resumen = resumen_diario()
    
    mensaje = "Resumen diario de las variaciones económicas:\n"
    mensaje += f"- Tipo de Cambio Minorista: {resumen['Resumen de variaciones']['Tipo de Cambio Minorista']}%\n"
    mensaje += f"- Tipo de Cambio Mayorista: {resumen['Resumen de variaciones']['Tipo de Cambio Mayorista']}%\n"
    mensaje += f"- Reservas Internacionales: {resumen['Resumen de variaciones']['Reservas Internacionales']}%\n"
    mensaje += f"- Tasa de Política Monetaria: {resumen['Resumen de variaciones']['Tasa de Política Monetaria']}%\n"
    
    # Enviar el mensaje automáticamente
    bot.send_message(TELEGRAM_CHAT_ID, mensaje)

# Función para configurar las alertas
def iniciar_alertas():
    obtener_valor_inicial()  # Establece el valor al inicio del día
    schedule.every().hour.do(comparar_dolar)  # Configura la alerta cada hora
    schedule.every().day.at("20:00").do(enviar_resumen_diario)  # Envía un resumen diario a las 8 p.m.

    while True:
        schedule.run_pending()
        time.sleep(1)

def iniciar_alertas():
    obtener_valor_inicial()  # Establece el valor al inicio del día

    # Para pruebas, puedes usar la programación cada minuto
    schedule.every().minute.do(comparar_dolar)  
    schedule.every().day.at("17:30").do(enviar_resumen_diario)  

    schedule.every().day.at("20:00").do(enviar_resumen_diario)  

    while True:
        schedule.run_pending()
        time.sleep(1)




# Si el bot recibe un mensaje no reconocido
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "¡No entiendo lo que quieres decirme! Usa los comandos /start o /help para obtener más información.")

# Main
if __name__ == "__main__":
    bot.polling(none_stop=True)