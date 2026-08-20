"""Generative UIとAX記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-08-21-generative-ui-agent-experience"

write_figure(SLUG, "ui-shift.svg", figure(
    "uishift",
    "UIの重心の移動",
    "従来のアプリケーションでは、人間が事前に作り込まれたUIを操作し、"
    "UIがAPIを呼び、APIがデータへ届くという一本の経路しかない。"
    "エージェント中心の構成では、人間はその場で生成されるUIと対話し、"
    "そのUIをAIエージェントが組み立てる。"
    "APIやデータとのやり取りは人間のUIを経由せず、エージェントが直接行う。",
    [Section(title="従来のアプリケーション", framed=True,
             nodes=[("h1", "人間"), ("ui1", "事前に作り込まれたUI"),
                    ("api1", "API"), ("db1", "データ")],
             edges=[("h1", "ui1"), ("ui1", "api1"), ("api1", "db1")],
             layers=[["h1"], ["ui1"], ["api1"], ["db1"]]),
     Section(title="エージェント中心の構成", framed=True,
             nodes=[("h2", "人間"), ("gen", "その場で生成されるUI", "cool"),
                    ("ag", "AIエージェント", "accent"), ("api2", "API・データ")],
             edges=[("h2", "gen", "対話", "both"), ("ag", "gen", "組み立て"),
                    ("ag", "api2", "直接やり取り")],
             layers=[["h2"], ["gen"], ["ag"], ["api2"]])]))

write_figure(SLUG, "genui-types.svg", figure(
    "gtypes",
    "Generative UIの3類型",
    "Static型はフロントエンドが定義済みの部品を持ち、エージェントはどれを出すか"
    "選んでデータを流し込むだけ。Declarative型はエージェントがUIの構成を"
    "データとして返し、クライアントが自分の部品で描画する。"
    "Open-ended型はエージェントがUI面そのものを返す。"
    "下へ行くほどエージェントの自由度が上がり、フロントエンドの制御が減る。",
    [Section(
        nodes=[("st", "Static型\n定義済み部品から選ぶ"),
               ("de", "Declarative型\nUIの構成をデータで返す", "accent"),
               ("op", "Open-ended型\nUI面そのものを返す", "warm")],
        edges=[("st", "de", "自由度が上がる", "dashed"),
               ("de", "op", "", "dashed")],
        layers=[["st"], ["de"], ["op"]])]))

write_figure(SLUG, "component-catalog.svg", figure(
    "catalog",
    "コンポーネントカタログによる描画",
    "エージェントはUIの構成を宣言的なJSONデータとして返す。"
    "そこから参照できるのはクライアントが事前に登録した"
    "コンポーネントカタログの部品だけで、"
    "描画はクライアント側が自分のスタイルで行う。"
    "実行可能なコードを受け取らないことで、UIインジェクションを避ける。",
    [Section(
        nodes=[("ag", "エージェント", "accent"),
               ("json", "UIの構成を記述したJSON"),
               ("cat", "コンポーネントカタログ\n登録済みの信頼できる部品"),
               ("ui", "描画されたUI", "cool")],
        edges=[("ag", "json", "宣言的に出力"),
               ("json", "cat", "登録部品だけ参照"),
               ("cat", "ui", "クライアントが描画")],
        layers=[["ag"], ["json"], ["cat"], ["ui"]])]))
