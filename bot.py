import requests
import time
from datetime import datetime, timezone
import json
import threading

# === CONFIGURAÇÃO ===
CONFIG_FILE = "config.json"

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
CHAT_ID = config["CHAT_ID"]
CURRENCY = config.get("vs_currency", "usd")
TOP_N = config.get("top_n", 50)
INTERVAL = config.get("interval_minutes", 30)
ALERT_THRESHOLD = config.get("alert_threshold_percent", 10)

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
PARAMS = {
    "vs_currency": CURRENCY,
    "order": "market_cap_desc",
    "per_page": TOP_N,
    "page": 1,
    "sparkline": False
}

last_prices = {}

# === FUNÇÃO: ENVIAR MENSAGEM ===
def send_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

# === FUNÇÃO: OBTER DADOS E ENVIAR RELATÓRIO ===
def get_market_data():
    try:
        data = requests.get(API_URL, params=PARAMS).json()
        now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

        compra, venda, estaveis, alertas = [], [], [], []

        for coin in data:
            name = coin["name"]
            price = coin["current_price"]
            change_24h = coin["price_change_percentage_24h"] or 0

            prev_price = last_prices.get(name, price)
            var_pct = ((price - prev_price) / prev_price) * 100 if prev_price != 0 else 0

            # Classificação simples
            if change_24h >= 1:
                compra.append(name)
            elif change_24h <= -1:
                venda.append(name)
            else:
                estaveis.append(name)

            # Alerta ±10%
            if abs(var_pct) >= ALERT_THRESHOLD:
                emoji = "🟢" if var_pct > 0 else "🔴"
                alertas.append(f"{emoji} <b>{name}</b> — variação de {var_pct:.2f}%")

            last_prices[name] = price

        # Mensagem principal formatada
        mensagem = f"""
📊 <b>Relatório — Top {TOP_N} Criptos</b>
🕒 Atualizado: <b>{now}</b>

🟢 <b>Indicadas para compra:</b><br>{', '.join(compra) if compra else '— Nenhuma'}

🔴 <b>Indicadas para venda:</b><br>{', '.join(venda) if venda else '— Nenhuma'}

⚪ <b>Estáveis / Não mexer:</b><br>{', '.join(estaveis) if estaveis else '— Nenhuma'}

💬 <i>Análise automática por ZacaroneBot</i>
"""
        send_message(mensagem)

        # Envia alerta se alguma cripto variar ±10%
        if alertas:
            alert_text = "<br>".join(alertas)
            send_message(f"🚨 <b>Alerta de Variação Instantânea (±{ALERT_THRESHOLD:.0f}%)</b><br><br>{alert_text}")

    except Exception as e:
        print(f"Erro ao obter dados: {e}")

# === LOOP PRINCIPAL ===
def start_bot():
    print("🤖 ZacaroneBot iniciado! Enviando atualizações a cada", INTERVAL, "minutos...")
    while True:
        get_market_data()
        time.sleep(INTERVAL * 60)

# Inicia o bot em thread separada
if __name__ == "__main__":
    thread = threading.Thread(target=start_bot)
    thread.start()
