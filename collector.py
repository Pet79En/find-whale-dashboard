import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from hyperliquid.info import Info
from hyperliquid.utils import constants
from evaluator import WhaleEvaluator
from ranker import CustomWhaleRanker

class HyperliquidCollector:
    def __init__(self):
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)

    def get_top_whales_addresses(self, max_count=100):
        addresses = []
        filepath = "myndx_matched_whales.csv"

        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                if "Address" in df.columns:
                    addresses = df["Address"].dropna().astype(str).tolist()
            except Exception as e:
                print(f"Erro ao ler CSV das carteiras: {e}")

        return addresses[:max_count]

    def _fetch_single_whale(self, addr, index, user_capital):
        try:
            user_state = self.info.user_state(addr) or {}
            user_fills = self.info.user_fills(addr) or []
        except Exception:
            user_state, user_fills = {}, []

        ranker = CustomWhaleRanker(user_capital)
        eval_data = WhaleEvaluator.evaluate_whale(user_fills, user_state, addr)
        eval_data["Rank HyperX"] = index + 1
        eval_data["Address"] = addr
        eval_data["HyperX score"] = ranker.score_whale(eval_data)
        
        return eval_data

    def get_evaluated_whales_batch(self, user_capital, limit=100):
        addresses = self.get_top_whales_addresses(max_count=limit)
        
        if not addresses:
            return pd.DataFrame()

        evaluated_list = []

        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [
                executor.submit(self._fetch_single_whale, addr, idx, user_capital)
                for idx, addr in enumerate(addresses)
            ]
            for future in futures:
                res = future.result()
                if res is not None:
                    evaluated_list.append(res)

        return pd.DataFrame(evaluated_list)