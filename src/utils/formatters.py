def moeda_brl(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def percentual(valor):
    try:
        return f"{float(valor):.1f}%".replace(".", ",")
    except Exception:
        return "0,0%"


def numero_br(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"


def nome_combustivel(valor):
    mapa = {
        "TODOS": "Todos",
        "GASOLINA_COMUM": "Gasolina comum",
        "GASOLINA_ADITIVADA": "Gasolina aditivada",
        "ETANOL": "Etanol",
        "DIESEL_S10": "Diesel S-10",
        "DIESEL_COMUM": "Diesel comum",
        "GNV": "GNV",
    }
    return mapa.get(str(valor), str(valor).replace("_", " ").title())


def badge_style(combustivel):
    combustivel = str(combustivel)

    if "ETANOL" in combustivel:
        return "background:#dcfce7;color:#166534;"
    if "GASOLINA" in combustivel:
        return "background:#fee2e2;color:#991b1b;"
    if "DIESEL" in combustivel:
        return "background:#fef9c3;color:#854d0e;"
    if "GNV" in combustivel:
        return "background:#dbeafe;color:#1d4ed8;"

    return "background:#e0e7ff;color:#3730a3;"