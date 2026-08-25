import pandas as pd

# 1. Carrega a lista completa da Hyperliquid e a lista curta da MYNDX
df_hyperx = pd.read_csv("hyperx_whales.csv")
df_myndx = pd.read_csv("myndx_short_wallets.csv")

# Identifica a coluna de endereços da Hyperliquid
col_addr = [c for c in df_hyperx.columns if "address" in c.lower() or "wallet" in c.lower()][0]

full_addresses = df_hyperx[col_addr].dropna().tolist()
short_prefixes = df_myndx["prefix"].dropna().tolist()

# 2. Busca a correspondência exata do prefixo (6 primeiros caracteres: '0x' + 4 hex)
matched_addresses = []
for prefix in short_prefixes:
    match = [addr for addr in full_addresses if addr.lower().startswith(prefix)]
    if match:
        matched_addresses.append(match[0]) # Adiciona o endereço completo correspondente

# 3. Salva a lista final completa das 100 carteiras para o seu projeto
df_final = pd.DataFrame({"Address": matched_addresses})
df_final.to_csv("myndx_matched_whales.csv", index=False)

print(f"Sucesso! {len(matched_addresses)} endereços completos foram associados e salvos em 'myndx_matched_whales.csv'.")