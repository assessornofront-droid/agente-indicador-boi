import json, smtplib, schedule, time, os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "assessornofront@gmail.com")
EMAIL_SENHA     = os.environ.get("EMAIL_SENHA", "kwjr kfbk qcjj xmak")
EMAIL_DESTINO   = os.environ.get("EMAIL_DESTINO", "rafael.oliveira@katinvest.com.br")
HORARIO_ENVIO   = "19:00"

DADOS_EXEMPLO = [
    {"nome": "Bahia",              "indicador": 319.65, "variacao":  1.05, "usd": 61.27},
    {"nome": "Goias",              "indicador": 330.62, "variacao": -0.59, "usd": 63.37},
    {"nome": "Mato Grosso",        "indicador": 338.87, "variacao": -0.46, "usd": 64.95},
    {"nome": "Mato Grosso do Sul", "indicador": 336.69, "variacao":  0.03, "usd": 64.54},
    {"nome": "Minas Gerais",       "indicador": 339.27, "variacao": -0.40, "usd": 65.03},
    {"nome": "Para",               "indicador": 326.20, "variacao":  0.89, "usd": 62.53},
    {"nome": "Rondonia",           "indicador": 305.64, "variacao": -1.34, "usd": 58.59},
    {"nome": "Sao Paulo",          "indicador": 348.55, "variacao": -0.43, "usd": 66.81},
    {"nome": "Tocantins",          "indicador": 325.09, "variacao": -0.23, "usd": 62.31},
]

def buscar_dados():
    import requests
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.indicadordoboi.com.br/"}
    for url in ["https://pec.datagro.com/pec/boi/boletim", "https://pec.datagro.com/pec/boi/today"]:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                d = normalizar(r.json())
                if d: return d
        except: pass
    return DADOS_EXEMPLO

def normalizar(raw):
    mapa = {"BA":"Bahia","GO":"Goias","MT":"Mato Grosso","MS":"Mato Grosso do Sul",
            "MG":"Minas Gerais","PA":"Para","RO":"Rondonia","SP":"Sao Paulo","TO":"Tocantins"}
    r = []
    if isinstance(raw, list):
        for item in raw:
            nome = mapa.get((item.get("state") or item.get("estado") or "").upper(),
                            item.get("state") or item.get("estado") or item.get("nome",""))
            def f(ks):
                for k in ks:
                    v = item.get(k)
                    if v is not None:
                        try: return float(str(v).replace(",",".").replace("%",""))
                        except: pass
                return 0.0
            if nome: r.append({"nome":nome,"indicador":f(["value","indicador","preco"]),
                                "variacao":f(["variation","variacao","var"]),"usd":f(["usd","dolar"])})
    return r or None

def fmt(v): return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def fv(v):
    s = "+" if v > 0 else ""
    return f"{s}{v:.2f}%".replace(".",",")

def gerar_html(dados):
    hoje = datetime.now().strftime("%d/%m/%Y")
    dia = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"][datetime.now().weekday()]
    linhas = ""
    for i, e in enumerate(dados):
        sp = "paulo" in e["nome"].lower()
        bg = "#FFFBEB" if sp else ("#F4F9F6" if i%2==0 else "#FFFFFF")
        fw = "700" if sp else "400"
        v = e["variacao"]
        cv = "#1a8a4a" if v >= 0 else "#cc2200"
        st = "▲" if v > 0 else ("▼" if v < 0 else "-")
        linhas += f'<tr style="background:{bg};"><td style="padding:13px 18px;font-size:14px;font-weight:{fw};color:#1a1a2e;border-bottom:1px solid #e8ede9;">{e["nome"]}</td><td style="padding:13px 18px;text-align:center;font-size:15px;font-weight:700;color:#1a2e1a;border-bottom:1px solid #e8ede9;">R$ {fmt(e["indicador"])}</td><td style="padding:13px 18px;text-align:center;font-size:14px;font-weight:700;color:{cv};border-bottom:1px solid #e8ede9;">{st} {fv(v)}</td><td style="padding:13px 18px;text-align:center;font-size:14px;color:#555;border-bottom:1px solid #e8ede9;">US$ {fmt(e["usd"])}</td></tr>'
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="margin:0;padding:0;background:#eef2ee;font-family:Arial,sans-serif;"><div style="max-width:620px;margin:32px auto;border-radius:14px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,0.13);"><div style="background:#1a5c38;padding:28px 32px;text-align:center;"><p style="margin:0 0 6px;color:#a8d5b8;font-size:11px;letter-spacing:3px;">DATAGRO PECUARIA</p><h1 style="margin:0 0 6px;color:#fff;font-size:26px;font-weight:700;">Indicador do Boi</h1><p style="margin:0;color:#c8e6d4;font-size:13px;">{dia}, {hoje}</p></div><div style="background:#fff;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#154360;"><th style="padding:12px 18px;text-align:left;color:#fff;font-size:12px;">Estado</th><th style="padding:12px 18px;text-align:center;color:#fff;font-size:12px;">Indicador R$/@</th><th style="padding:12px 18px;text-align:center;color:#fff;font-size:12px;">Variacao</th><th style="padding:12px 18px;text-align:center;color:#fff;font-size:12px;">USD</th></tr></thead><tbody>{linhas}</tbody></table></div><div style="background:#f4f8f5;padding:18px 24px;border-top:2px solid #d0e4d5;"><p style="margin:0;font-size:11px;color:#666;">* Media a VISTA ponderada ate 3 dias uteis | Horario UTC-3 ate 16:30 | <a href="https://www.indicadordoboi.com.br" style="color:#1a5c38;">indicadordoboi.com.br</a></p><p style="margin:6px 0 0;font-size:10px;color:#aaa;">Enviado automaticamente as 19h - Agente Indicador do Boi</p></div></div></body></html>'

def enviar(dados):
    hoje = datetime.now().strftime("%d/%m/%Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Indicador do Boi DATAGRO - {hoje}"
    msg["From"] = f"Agente Boi Gordo <{EMAIL_REMETENTE}>"
    msg["To"] = EMAIL_DESTINO
    msg.attach(MIMEText(gerar_html(dados), "html", "utf-8"))
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.ehlo(); s.starttls(); s.login(EMAIL_REMETENTE, EMAIL_SENHA); s.send_message(msg)
    print(f"OK - Email enviado {datetime.now()}")

def executar():
    print(f"== {datetime.now().strftime('%d/%m/%Y %H:%M')} ==")
    dados = buscar_dados()
    enviar(dados)

schedule.every().day.at(HORARIO_ENVIO).do(executar)
print(f"Agente rodando. Envio diario as {HORARIO_ENVIO}.")
while True:
    schedule.run_pending()
    time.sleep(60)
