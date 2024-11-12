# Bot Económico de Telegram

Este es un bot de Telegram diseñado para proporcionar información económica en tiempo real, como el tipo de cambio del dólar oficial y blue, así como también las principales variables que brinda el Banco Central de la República Argentina (BCRA).

# Características

1) Consulta del dólar oficial: Obtiene el tipo de cambio oficial del dólar según la API del BCRA.
2) Consulta del dólar blue: Proporciona el tipo de cambio del dólar blue, incluyendo tanto el valor de compra como el de venta.
3) Consulta del dólar tarjeta: Proporciona el tipo de cambio del dolar tarjeta, incluyendo el valor de la compra como el de venta.
4) Consultar gráficas de las principales variables de la economía Argentina

# Requisitos

- Python 3.x
# Librerías:
- requests: Para realizar las solicitudes HTTP a las APIs.
- python-telegram-bot o telebot: Para interactuar con la API de Telegram.
- python-dotenv: Para gestionar las claves API a través de un archivo .env.

# Como utilizar el bot desde tu entorno. 

1) Instalar dependencias =>  pip install requests python-dotenv pyTelegramBotAPI Flask
2) Crear un .env donde colocar tus credenciales
3) En el archivo .env usar "TELEGRAM_BOT_TOKEN=tu_token_de_telegram", "API_BCRA_TOKEN=tu_token_de_la_api_bcra" y TELEGRAM_CHAT_ID (el último podes usarlo solo si creas un bot propio con bot-father)
4) Ejecutar el bot.

# ¿Qué APIS fueron usadas?

- https://api.bcra.gob.ar
- https://dolarapi.com
- https://www.estadisticasbcra.com
