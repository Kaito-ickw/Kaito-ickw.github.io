"""Graph Engineering記事の図。"""
from common import MUTED, S1, S2, S3
from diagram import Section, figure, nested, write_figure

SLUG = "2026-07-27-graph-engineering-agent-systems"

write_figure(SLUG, "graph-types.svg", figure(
    "gtypes",
    "実行グラフとKnowledge Graphの違い",
    "実行グラフはIssue取得・調査・分岐・公開のように手順が一列につながり、"
    "ノードを辿って処理を進める。"
    "Knowledge GraphやGraphRAGは、Claude CodeがGitHubをuses、"
    "GitHubがPull Requestをproduces、Claude CodeがCLAUDE.mdにconstrained_byという"
    "関係で結ばれる意味構造であり、辿るというより問い合わせて使う。",
    [Section(title="実行グラフ（本記事の対象）", framed=True,
             nodes=[("e1", "Issue取得"), ("e2", "調査"), ("e3", "分岐"), ("e4", "公開")],
             edges=[("e1", "e2"), ("e2", "e3"), ("e3", "e4")],
             layers=[["e1", "e2", "e3", "e4"]]),
     Section(title="Knowledge Graph / GraphRAG", framed=True,
             nodes=[("k1", "Claude Code", "accent"), ("k2", "GitHub"),
                    ("k3", "Pull Request"), ("k4", "CLAUDE.md")],
             edges=[("k1", "k2", "uses"), ("k2", "k3", "produces"),
                    ("k1", "k4", "constrained_by")])]))

write_figure(SLUG, "design-grain.svg", nested(
    "grain",
    "設計する粒度の入れ子関係",
    "Prompt Engineeringを最も内側に、Context Engineering、"
    "Loop / Harness Engineering、Graph Engineeringの順で外側へ入れ子になる。"
    "外側が内側を置き換えるのではなく内包する関係にある。",
    [("Graph Engineering", "複数loop・通常コード・人間・評価", S1, "#eef4fc"),
     ("Loop / Harness Engineering", "1つのAgent loopの安定動作", S3, "#eef8f4"),
     ("Context Engineering", "入力に添える情報", S2, "#fdf1eb"),
     ("Prompt Engineering", "1回の入力", MUTED, "#f2f1ee")]))

write_figure(SLUG, "workflow-vs-agent.svg", figure(
    "wfag",
    "WorkflowとAgentの違い",
    "Workflowは事前定義したコードパスの上でLLMを呼び、次のステップも固定されている。"
    "Agentは目的とツールを渡し、LLMが次の行動を決め、"
    "完了したかを判定して未完了なら決定へ戻る。",
    [Section(title="Workflow", framed=True,
             nodes=[("w1", "事前定義したコードパス"), ("w2", "LLM呼び出し"),
                    ("w3", "次のステップも固定")],
             edges=[("w1", "w2"), ("w2", "w3")]),
     Section(title="Agent", framed=True,
             nodes=[("a1", "目的とツールを渡す"), ("a2", "LLMが次の行動を決定", "accent"),
                    ("a3", "完了したか", "decision"), ("a4", "終了")],
             edges=[("a1", "a2"), ("a2", "a3"),
                    ("a3", "a2", "いいえ"), ("a3", "a4", "はい")])]))

write_figure(SLUG, "execution-models.svg", figure(
    "models",
    "既存の実行モデルとGraph Engineeringの関係",
    "有限状態機械やStatechart、DAGとワークフローエンジン、Durable Execution、"
    "Actor modelやEvent-drivenといった決定的な実行モデルの延長に、"
    "ノードの一部にAgent loopを含むGraph Engineeringがある。"
    "そこでは停止条件・冪等性・評価・権限・コストが新たに重要になる。",
    [Section(title="決定的な実行モデル", framed=True,
             chips=["有限状態機械 / Statechart", "DAG / ワークフローエンジン",
                    "Durable Execution", "Actor model / Event-driven"]),
     Section(nodes=[("ge", "Graph Engineering\nノードの一部にAgent loopを含む", "accent"),
                    ("new", "新たに重要になる観点\n停止条件・冪等性・評価・権限・コスト")],
             edges=[("ge", "new")])]))

write_figure(SLUG, "article-pipeline.svg", figure(
    "pipe",
    "記事作成パイプラインの前半",
    "Issueが作られると通常コードがIssueを解析し、LLMかルールで依頼タイプを分類する。"
    "調査が要らなければそのまま構成作成へ進み、"
    "必要ならAgent loopがWeb調査をしてから構成作成へ合流する。"
    "構成ができたら通常コードで記事を作成する。",
    [Section(
        nodes=[("start", "Issue作成", "accent"), ("parse", "Issue解析\n通常コード"),
               ("cls", "依頼タイプ分類\nLLM or ルール", "decision"),
               ("research", "Web調査\nAgent loop", "cool"),
               ("compose", "構成作成"), ("write", "記事作成\n通常コード")],
        edges=[("start", "parse"), ("parse", "cls"),
               ("cls", "research", "調査必要"), ("research", "compose"),
               ("cls", "compose", "調査不要"),
               ("compose", "write")],
        layers=[["start"], ["parse"], ["cls"], ["research"], ["compose"], ["write"]],
    )]))

write_figure(SLUG, "article-pipeline-verify.svg", figure(
    "pipe2",
    "記事作成パイプラインの後半",
    "Jekyllのビルドが失敗したらAgent loopが自動修正してビルドへ戻る。"
    "成功したらルールとLLMで品質を評価し、不合格なら自動修正へ戻す。"
    "合格したらGitHub APIでPRを作り、人間のレビューと承認へ渡す。",
    [Section(
        nodes=[("build", "Jekyll build\n通常コード", "accent"),
               ("fix", "自動修正\nAgent loop", "warm"),
               ("eval", "品質評価\nRule + LLM", "decision"),
               ("pr", "PR作成\nGitHub API"), ("human", "人間レビュー・承認", "cool")],
        edges=[("build", "fix", "失敗"), ("fix", "build"),
               ("build", "eval", "成功"), ("eval", "fix", "不合格"),
               ("eval", "pr", "合格"), ("pr", "human")],
        layers=[["build"], ["fix"], ["eval"], ["pr"], ["human"]],
    )]))

write_figure(SLUG, "when-graph.svg", figure(
    "when",
    "Graph Engineeringとして設計するかの判断",
    "分岐・再試行・中断再開がなければ通常コードのままでよい。"
    "あるなら、複数のツールや複数のAgent loopがあるかを見る。"
    "なければLoop / Harness Engineeringで足りる。"
    "あるなら、人間承認・監査・コストや権限の制御が必要かを見て、"
    "必要ならGraph Engineeringとして設計する。",
    [Section(
        nodes=[("q1", "分岐・再試行・中断再開があるか", "decision"),
               ("code", "通常コードのままでよい", "plain"),
               ("q2", "複数のツール・複数のAgent loopがあるか", "decision"),
               ("loop", "Loop / Harness Engineeringで足りる"),
               ("q3", "人間承認・監査・コストや権限の制御が必要か", "decision"),
               ("graph", "Graph Engineeringとして設計する", "accent")],
        edges=[("q1", "code", "なし"), ("q1", "q2", "あり"),
               ("q2", "loop", "なし"), ("q2", "q3", "あり"),
               ("q3", "loop", "なし"), ("q3", "graph", "あり")],
        # 「なし」で降り、「あり」で次の問いへ進む階段にする。
        layers=[["q1"], ["code", "q2"], ["loop", "q3"], ["graph"]],
    )]))
