from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st


def render_update_status(interval_seconds: int):
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))

    st.markdown(
        f"""
        <div style="
            background:#111827;
            border:1px solid #334155;
            border-radius:12px;
            padding:10px 14px;
            margin-bottom:18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
        ">
            <span style="color:#94a3b8;font-size:0.82rem;font-weight:700;">
                🔄 Atualização automática a cada {interval_seconds} segundos
            </span>
            <span style="color:#f8fafc;font-size:0.82rem;font-weight:800;">
                Última atualização: {agora.strftime("%d/%m/%Y %H:%M:%S")}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )