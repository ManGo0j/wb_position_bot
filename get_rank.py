import json
import requests
from get_token import get_token

HEADERS = {
    'accept': '*/*',
    'accept-language': 'ru-RU,ru;q=0.9',
    'priority': 'u=1, i',
    'referer': 'https://www.wildberries.ru/catalog/0/search.aspx',
    'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'x-spa-version': '13.15.1',
    'x-userid': '0',
}

class WbRank:
    SEARCH_URL = "https://www.wildberries.ru/__internal/u-search/exactmatch/sng/common/v18/search"

    DEFAULT_PARAMS = {
        "ab_testing": ["false", "false"],
        "appType": "1",
        "curr": "rub",
        "dest": "-3626404",
        "hide_dtype": "11",
        "inheritFilters": "false",
        "lang": "ru",
        "page": "1",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
        "suppressSpellcheck": "false",
    }

    def __init__(self, goods: list):
        self.goods = goods
        self._update_token()

    def _update_token(self):
        self.token = get_token()

    def get_fetch(self, query: str, retries: int = 2):
        params = self.DEFAULT_PARAMS.copy()
        params["query"] = query

        for attempt in range(1, retries + 2):
            try:
                response = requests.get(
                    self.SEARCH_URL,
                    params=params,
                    cookies={"x_wbaas_token": self.token},
                    headers=HEADERS
                )
                
                # Если вдруг токен протух во время работы (редко, но бывает)
                if response.status_code == 498:
                    self._update_token()
                    continue
                
                if response.status_code != 200:
                    return None

                return response.json()
            except Exception:
                return None
        return None

    def get_rank_position(self, data: json, sku: str | int) -> int | None:
        products = data.get("products")
        if not products:
            return None

        try:
            sku = int(sku)
        except ValueError:
            return None

        for index, product in enumerate(products, start=1):
            if product.get("id") == sku:
                return index
        return None

    def parse_rank(self) -> list:
        results = []
        for good in self.goods:
            sku = good.get("sku")
            query = good.get("query")

            if not sku or not query:
                continue

            data = self.get_fetch(query=query)
            if not data:
                results.append({"sku": sku, "query": query, "rank": None})
                continue

            results.append(
                {"sku": sku, "query": query, "rank": self.get_rank_position(data=data, sku=sku)}
            )
        return results

if __name__ == "__main__":
    try:
        user_sku = input("Введите артикул: ").strip()
        user_query = input("Введите поисковый запрос: ").strip()

        if user_sku and user_query:
            input_data = [{"sku": user_sku, "query": user_query}]
            
            ranker = WbRank(goods=input_data)
            results = ranker.parse_rank()
            
            if results:
                res = results[0]
                rank = res.get("rank")
                if rank:
                    print(f"✅ Артикул {res['sku']} по запросу '{res['query']}' находится на {rank} месте.")
                else:
                    print(f"😔 Артикул {res['sku']} по запросу '{res['query']}' не найден (или ошибка доступа).")
        else:
            print("Ошибка: пустой ввод.")
            
    except KeyboardInterrupt:
        print("\nВыход.")