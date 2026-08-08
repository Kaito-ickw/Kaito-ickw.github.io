"""川邊健太郎のAIソロプレナー起業の記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-08-07-kawabe-ai-solopreneur"

write_figure(SLUG, "scope-order.svg", figure(
    "scopeorder",
    "事業スコープを決める順序の違い",
    "よくある順序では、先に事業を決め、そこへAIを入れ、AIができない部分を人が埋める。"
    "埋めた部分はそのまま運用へ残り、恒久的な人手として固定化する。"
    "川邊健太郎が置いた順序では、先にAIができる範囲を確認し、その内側で事業を切る。"
    "人が必要だと分かった事業は一旦やめる。",
    [Section(title="よくある順序", framed=True,
             nodes=[("a1", "事業を決める"),
                    ("a2", "AIを入れる"),
                    ("a3", "できない部分を\n人が埋める"),
                    ("a4", "人手が固定化する", "warm")],
             edges=[("a1", "a2"), ("a2", "a3"), ("a3", "a4")]),
     Section(title="川邊が置いた順序", framed=True,
             nodes=[("b1", "AIにできる範囲を\n確認する", "accent"),
                    ("b2", "その内側で\n事業を切る"),
                    ("b3", "人が要ると分かれば\n一旦やめる", "cool")],
             edges=[("b1", "b2"), ("b2", "b3")])]))
