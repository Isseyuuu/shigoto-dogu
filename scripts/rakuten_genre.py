"""楽天のジャンルIDを確定させる。

キーワード検索は表記ゆれで取りこぼす一方、ジャンル指定は対象カテゴリを漏れなく
拾える。ただしジャンルIDを推測で決めると別カテゴリを集計してしまうため、必ず
このスクリプトで階層を降りて名前を目視確認してから使うこと。

使い方:
    python scripts/rakuten_genre.py            # ルートから直下を表示
    python scripts/rakuten_genre.py 101070     # 指定ジャンルの直下を表示
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

from rakuten_fetch import credentials

ENDPOINT = "https://openapi.rakuten.co.jp/ichibams/api/IchibaGenre/Search/20120723"


def main():
    genre_id = sys.argv[1] if len(sys.argv) > 1 else "0"
    app_id, access_key, _ = credentials()
    params = {
        "applicationId": app_id,
        "accessKey": access_key,
        "genreId": genre_id,
        "format": "json",
    }
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "shigoto-dogu/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}")

    current = data.get("current") or {}
    print(f"現在地: {current.get('genreName', '(ルート)')} (id={current.get('genreId', 0)})\n")

    parents = data.get("parents") or []
    if parents:
        trail = " > ".join(p["parent"]["genreName"] for p in parents)
        print(f"上位: {trail}\n")

    children = data.get("children") or []
    if not children:
        print("直下のジャンルはありません(末端カテゴリ)。")
        return
    print("直下のジャンル:")
    for c in children:
        child = c.get("child", c)
        print(f"  {child['genreId']:>10}  {child['genreName']}")
    print("\n目的のジャンル名を確認し、そのIDで再度このスクリプトを実行して末端まで降りてください。")


if __name__ == "__main__":
    main()
