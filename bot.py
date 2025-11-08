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
CURRENCY = config.get("vs_currency", "brl")
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
        r = requests.post(url, json=payload)
        print("📩 Resposta Telegram:", r.text)
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")

# === FUNÇÃO: GERA RELATÓRIO ===
def get_market_data():
    try:
        response = requests.get(API_URL, params=PARAMS)
        if response.status_code != 200:
            print("❌ Erro ao buscar dados:", response.text)
            return

        data = response.json()
        now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        report_lines = []
        alerts = []

        for coin in data:
            name = coin["name"]
            symbol = coin["symbol"].upper()
            price = coin["current_price"]
            prev_price = last_prices.get(name, price)
            change_value = price - prev_price
            change_pct = ((price - prev_price) / prev_price) * 100 if prev_price else 0

            if change_value > 0.5:
                status = f"🟢 <b>{name} ({symbol})</b> — Subiu R$ {change_value:,.2f} (+{change_pct:.2f}%) → <b>Indicado venda (lucro)</b>"
            elif change_value < -0.5:
                status = f"🔴 <b>{name} ({symbol})</b> — Caiu R$ {abs(change_value):,.2f} ({change_pct:.2f}%) → <b>Indicado compra (queda)</b>"
            else:
                status = f"⚪ <b>{name} ({symbol})</b> — Sem variação significativa → <b>Indicado manter (estável)</b>"

            if abs(change_pct) >= ALERT_THRESHOLD:
                emoji = "🟢" if change_pct > 0 else "🔴"
                alerts.append(f"{emoji} {name} ({symbol}) — variação de {change_pct:.2f}%")

            last_prices[name] = price
            report_lines.append(status)

        header = (
            f"📊 <b>Relatório — Top {TOP_N} Criptos</b>\n"
            f"🕒 Atualizado: <b>{now}</b>\n\n"
            f"📈 Comparativo com o ciclo anterior (últimos {INTERVAL} min):\n\n"
        )

        footer = "\n\n💬 <i>Análise automática por SmartCryptoBot</i>"
        full_report = header + "\n".join(report_lines) + footer

        # Envia relatório principal
        send_message(full_report)

        # Envia alerta especial se houver variação grande
        if alerts:
            alert_text = "\n".join(alerts)
            alert_msg = (
                f"🚨 <b>Alerta de Variação Relevante (±{ALERT_THRESHOLD:.0f}%)</b>\n\n{alert_text}"
            )
            send_message(alert_msg)

        print(f"✅ Relatório enviado com sucesso ({len(report_lines)} criptos).")

    except Exception as e:
        print(f"❌ Erro ao processar dados: {e}")

# === LOOP PRINCIPAL ===
def start_bot():
    print(f"🤖 SmartCryptoBot iniciado! Enviando atualizações a cada {INTERVAL} minutos...")
    get_market_data()  # primeira mensagem imediata
    while True:
        print("📡 Coletando novos dados de mercado...")
        get_market_data()
        print("✅ Ciclo concluído. Aguardando próximo intervalo.\n")
        time.sleep(INTERVAL * 60)

if __name__ == "__main__":
    thread = threading.Thread(target=start_bot)
    thread.start()
