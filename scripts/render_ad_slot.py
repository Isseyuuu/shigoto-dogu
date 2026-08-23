"""選定済み商品を記事の広告枠HTMLへ描画する。

記事側の枠は次のマーカーで囲まれている。マーカーは描画後も残すので、価格や
レビュー件数が動いたら同じコマンドを再実行するだけで更新できる(再実行可能)。

    <!-- RAKUTEN_AD_SLOT: <slot名> ... -->  ... 中身 ...  <!-- /RAKUTEN_AD_SLOT -->

初回は中身ごとコメントで封じてあるため、描画時にコメントを開いて公開状態にする。
affiliateUrl が空の商品は掲載しない(踏んでも成果にならないリンクを置かない)。

使い方:
    python scripts/render_ad_slot.py --dry-run
    python scripts/render_ad_slot.py
"""
import argparse
import html
import json
import re
import sys

START = re.compile(r"<!--\s*RAKUTEN_AD_SLOT:\s*(?P<slot>[\w-]+)(?P<rest>.*?)-->", re.S)
END_MARK = "<!-- /RAKUTEN_AD_SLOT -->"
OLD_END = re.compile(r"/RAKUTEN_AD_SLOT\s*-->")


def esc(v):
    return html.escape(str(v), quote=True)


def card(item):
    stars = f"{item['reviewAverage']:.2f}"
    price = f"{item['itemPrice']:,}"
    name = esc(item["itemName"])
    return f"""      <div class="ad-card">
        <strong>{name}</strong>
        <img src="{esc(item['imageUrl'])}" alt="{name}" width="200" height="200" loading="lazy" decoding="async">
        <small>楽天市場価格の目安：{price}円（{esc(item['taxNote'])}・{esc(item['postageNote'])}・変動あり）</small>
        <small>楽天市場のレビュー：★{stars}（{item['reviewCount']:,}件、楽天市場の集計値）</small>
        <a href="{esc(item['affiliateUrl'])}" rel="sponsored nofollow">楽天市場で見る</a>
      </div>"""


def block(items, heading, fetched_at):
    date = (fetched_at or "")[:10]
    cards = "\n".join(card(i) for i in items)
    return f"""<div class="cta" id="shoes-picks">
      <p class="tag">広告</p>
      <h2>{esc(heading)}</h2>
      <p class="source-note">レビュー件数・平均評価は<strong>楽天市場の集計値</strong>であり、
      当サイトが実測したものではありません。掲載は{esc(date)}時点のデータです。価格・在庫・
      送料条件は変動するため、必ず商品ページで最新の条件を確認してください。</p>
      <div class="ad-options">
{cards}
      </div>
    </div>"""


def main():
    p = argparse.ArgumentParser(description="広告枠の描画")
    p.add_argument("--src", default="data/running_shoes_selected.json")
    p.add_argument("--article", default="articles/running-beginner-gear.html")
    p.add_argument("--slot", default="running-shoes")
    p.add_argument("--count", type=int, default=4, help="掲載点数")
    p.add_argument("--heading", default="レビューが多いランニングシューズ（楽天市場）")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    data = json.load(open(args.src, encoding="utf-8"))
    items = [i for i in data["items"] if i.get("affiliateUrl")][: args.count]
    if not items:
        sys.exit("affiliateUrl を持つ商品がありません。掲載を中止します。")
    skipped = len(data["items"]) - len([i for i in data["items"] if i.get("affiliateUrl")])
    if skipped:
        print(f"注意: affiliateUrl が空の商品を{skipped}件除外しました。")

    raw = open(args.article, encoding="utf-8", newline="").read()
    # 枠は2つの状態を取る。初回は中身ごと1つのコメントに封じられており、描画後は
    # 開始/終了マーカーが別々のコメントとして残る。どちらでも同じ範囲を置換できるよう、
    # 開始マーカーの位置から終了マーカーの終わりまでを丸ごと差し替える。
    m = re.search(r"<!--\s*RAKUTEN_AD_SLOT:\s*" + re.escape(args.slot) + r"(?![\w-])", raw)
    if not m:
        sys.exit(f"{args.article} に RAKUTEN_AD_SLOT: {args.slot} が見つかりません。")
    end = OLD_END.search(raw, m.end())
    if not end:
        sys.exit("終了マーカー /RAKUTEN_AD_SLOT が見つかりません。")

    new_block = (
        f"<!-- RAKUTEN_AD_SLOT: {args.slot} 自動生成。更新は "
        f"scripts/render_ad_slot.py を再実行する -->\n    "
        + block(items, args.heading, data.get("fetchedAt"))
        + f"\n    {END_MARK}"
    )
    updated = raw[: m.start()] + new_block + raw[end.end():]

    print(f"掲載 {len(items)}件:")
    for i in items:
        print(f"  ★{i['reviewAverage']:.2f} ({i['reviewCount']:,}件) {i['itemPrice']:,}円  {i['itemName'][:44]}")
    if args.dry_run:
        print("\n--dry-run のため書き込みませんでした。")
        return
    open(args.article, "w", encoding="utf-8", newline="").write(updated)
    print(f"\n{args.article} を更新しました(公開状態)。")


if __name__ == "__main__":
    main()
