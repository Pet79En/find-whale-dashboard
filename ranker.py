class CustomWhaleRanker:
    def __init__(self, user_capital):
        self.user_capital = user_capital

    def score_whale(self, data):
        # 1. Recência do Último Trade
        last_trade_hours = data.get("Last_Trade_Hours", 24)
        score_recency = max(0, 100 - (last_trade_hours * 2))

        # 2. Posições contra vs a favor do regime
        long_bias = data.get("Long_Bias_num", 50.0)
        is_bullish = long_bias >= 50.0
        open_longs = data.get("Open_Longs", 0)
        open_shorts = data.get("Open_Shorts", 0)

        if is_bullish:
            score_positions = (open_longs * 10) - (open_shorts * 15)
        else:
            score_positions = (open_shorts * 10) - (open_longs * 15)

        # 3. Ativos abertos
        active_assets = data.get("Active_Assets_Count", 0)
        if active_assets == 0:
            score_assets = 0
        else:
            score_assets = max(0, 100 - (active_assets - 1) * 15)

        # 4. Demais pontuações
        win_rate = data.get("Win_Rate_num", 50.0)
        liq_factor = min(100, data.get("Liq_Factor_num", 20.0) * 2.5)
        
        dca = data.get("DCA_Index", "")
        score_dca = 100 if "Baixo" in dca else (50 if "Moderado" in dca else 0)

        # PnL e Total Value
        pnl = data.get("PnL_num", 0)
        score_pnl = min(100, (pnl / 50000.0) * 100) if pnl >= 0 else max(-100, (pnl / 25000.0) * 100)

        total_val = data.get("Total_value_num", 0)
        score_val = min(100, (total_val / 100000.0) * 100)

        lev = data.get("Alavancagem", 2.0)
        score_lev = max(0, 100 - abs(lev - 2.0) * 25)

        # Score final ponderado
        total_score = (
            (score_recency * 0.15) +
            (score_positions * 0.10) +
            (score_assets * 0.10) +
            (win_rate * 0.20) +
            (liq_factor * 0.15) +
            (score_dca * 0.10) +
            (score_pnl * 0.10) +
            (score_lev * 0.10)
        )

        return round(max(0.0, min(100.0, total_score)), 1)