import streamlit as st
import pandas as pd
import subprocess
from collector import HyperliquidCollector

st.set_page_config(page_title="HyperX Custom Whale Evaluator", layout="wide")
st.title("🐋 Dashboard de Avaliação & Copy Trading Personalizado - MyndX / HyperX")

# ==========================================
# PAINEL ESQUERDO: CENÁRIO SIMULADO & COMANDOS
# ==========================================
st.sidebar.header("🎯 Cenário Simulado")

saldo_perpetuos = st.sidebar.number_input(
    "Saldo em Perpétuos ($)", 
    value=4000, 
    step=500, 
    help="Preenchimento manual do seu saldo total na corretora."
)

st.sidebar.markdown("---")
st.sidebar.header("🔄 Automação MyndX")

# Botão para re-executar o cross.py e atualizar os dados da MyndX
if st.sidebar.button("⚡ Atualizar Wallets MyndX", use_container_width=True):
    with st.spinner("Realizando cruzamento de endereços MyndX/HyperX..."):
        try:
            result = subprocess.run(["python", "cross.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.sidebar.success("Cruzamento concluído com sucesso!")
                st.cache_data.clear() # Limpa o cache para recarregar a tabela
            else:
                st.sidebar.error(f"Erro no cross.py: {result.stderr}")
        except Exception as e:
            st.sidebar.error(f"Falha ao executar: {e}")

@st.cache_data(ttl=300)
def load_whales_data(capital):
    collector = HyperliquidCollector()
    return collector.get_evaluated_whales_batch(capital, limit=100)

with st.spinner("Processando varredura das carteiras..."):
    df_raw = load_whales_data(saldo_perpetuos)

# ==========================================
# CÁLCULOS E SELEÇÃO DE COPY SETUP (PAINEL ESQUERDO)
# ==========================================
wallet_options = df_raw["Address"].tolist() if not df_raw.empty else []
selected_wallets = st.sidebar.multiselect(
    "Selecione as Wallets para o Copy Setup:",
    options=wallet_options,
    default=wallet_options[:2] if len(wallet_options) >= 2 else wallet_options
)

num_wallets = len(selected_wallets)
if num_wallets > 0:
    saldo_max_destinado = round(saldo_perpetuos * 0.85, 2)
    posicoes_simultaneas = num_wallets * 4
    capital_por_posicao = round(saldo_max_destinado / posicoes_simultaneas, 2)
else:
    saldo_max_destinado, posicoes_simultaneas, capital_por_posicao = 0.0, 0, 0.0

st.sidebar.markdown("---")
st.sidebar.metric("Saldo máx destinado", f"${saldo_max_destinado:,.2f}")
st.sidebar.metric("Posições simultâneas", f"{posicoes_simultaneas} posições")

if num_wallets > 0:
    setup_data = []
    for w_addr in selected_wallets:
        w_row = df_raw[df_raw["Address"] == w_addr].iloc[0] if not df_raw.empty and w_addr in df_raw["Address"].values else {}
        lev = w_row.get("Alavancagem", 1.5)
        lev_ideal = max(1.0, min(float(lev) if isinstance(lev, (int, float)) else 1.5, 3.0))
        addr_abbr = f"{w_addr[:6]}...{w_addr[-5:]}" if len(w_addr) > 11 else w_addr
        
        setup_data.append({
            "Wallet": addr_abbr,
            "Capital ($)": capital_por_posicao,
            "Alavancagem": f"{lev_ideal:.1f}x",
            "Teto": "2.0x"
        })
    
    st.sidebar.subheader("📋 Configuração Individual (MyndX)")
    st.sidebar.dataframe(pd.DataFrame(setup_data), use_container_width=True, hide_index=True)

# ==========================================
# PAINEL PRINCIPAL: TABELA COM MULTIHEADER
# ==========================================
if not df_raw.empty:
    st.subheader(f"📊 Curadoria e Ranking MyndX ({len(df_raw)} Baleias Analisadas)")
    
    df_sorted = df_raw.rename(columns={"HyperX score": "My Score"}).sort_values(by="My Score", ascending=False).copy()
    
    columns_tuples = [
        ("Resultado", "My Score"),
        ("Informações", "Address"),
        ("Tático (Order History)", "Last_Trade_Hours"),
        ("Tático (Order History)", "Active_Assets_Count"),
        ("Positions", "Open_Longs"),
        ("Positions", "Open_Shorts"),
        ("Positions", "Win_Rate"),
        ("Positions", "Liquidation_Factor"),
        ("Tático (Order History)", "DCA_Index"),
        ("Tático (Order History)", "Statistical_significance"),
        ("Tático (Order History)", "Tactical_is_bot"),
        ("Tático (Order History)", "Notional"),
        ("Tático (Order History)", "Long Bias (exposure)"),
        ("Perfil Macro", "PnL"),
        ("Perfil Macro", "Total_value"),
        ("Perfil Macro", "Alavancagem"),
        ("Tático (Order History)", "alignment_q10")
    ]
    
    cols_flat = [t[1] for t in columns_tuples]
    df_display = df_sorted[cols_flat].copy()
    df_display.columns = pd.MultiIndex.from_tuples(columns_tuples)

    # Estilização para destacar em vermelho posições contra a tendência
    def style_against_trend(df):
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        for idx in df.index:
            bias_str = str(df_sorted.loc[idx, "Long Bias (exposure)"]).replace('%', '')
            bias = float(bias_str) if bias_str != 'nan' else 50.0
            
            if bias >= 50.0:
                styles.loc[idx, ("Positions", "Open_Shorts")] = 'color: red; font-weight: bold;'
            else:
                styles.loc[idx, ("Positions", "Open_Longs")] = 'color: red; font-weight: bold;'
        return styles

    st.dataframe(df_display.style.apply(style_against_trend, axis=None), use_container_width=True)
    
    st.markdown("### 📋 Copiar Endereço Selecionado")
    c1, c2 = st.columns([2.4, 1.6])
    with c1:
        target_addr = st.selectbox("Escolha uma carteira para copiar o endereço completo:", options=df_sorted["Address"].tolist())
    with c2:
        st.write("")
        st.write("")
        st.code(target_addr, language="text")

else:
    st.warning("O arquivo 'myndx_matched_whales.csv' não foi encontrado. Clique em '⚡ Atualizar Wallets MyndX' na barra lateral.")