"""Tools / Resources / Prompts の記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-19-mcp-tools-resources-prompts"

write_figure(SLUG, "server-primitives.svg", figure(
    "prims",
    "MCP Serverが公開する3つのprimitive",
    "MCP ServerはTools・Resources・Promptsの3つを公開する。"
    "Toolsは実行可能な機能でModelが選び、Resourcesは参照するデータでApplicationが文脈を管理し、"
    "Promptsは再利用する指示でUserが明示的に選ぶ。",
    [Section(
        nodes=[("server", "MCP Server", "accent"),
               ("tools", "Tools\n実行可能な機能"),
               ("res", "Resources\n参照するデータ"),
               ("prompts", "Prompts\n再利用する指示")],
        edges=[("server", "tools"), ("server", "res"), ("server", "prompts")],
    ),
     Section(title="選ぶ主体", framed=True, chip_style="plain",
             chips=["Tools → Model", "Resources → Application", "Prompts → User"])]))

write_figure(SLUG, "client-primitives.svg", figure(
    "cliprims",
    "MCP Clientが提供する3つのprimitive",
    "MCP ClientはRootsで対象ディレクトリを公開し、Samplingでモデル利用を仲介し、"
    "Elicitationでユーザー操作を仲介する。"
    "Server側はroots/list・sampling/createMessage・elicitation/createで呼び出す。",
    [Section(
        # 3本の辺に横並びのラベルを付けると同じ高さで衝突する。役割はノード側へ入れる。
        nodes=[("client", "MCP Client", "accent"),
               ("roots", "Roots\n対象ディレクトリ\n公開・提供"),
               ("sampling", "Sampling\nLLM生成\nモデル利用を仲介"),
               ("elicit", "Elicitation\n追加情報\n操作を仲介")],
        edges=[("client", "roots"), ("client", "sampling"), ("client", "elicit")],
    ),
     Section(title="Serverから呼ぶメソッド", framed=True, chip_style="plain",
             chips=["roots/list", "sampling/createMessage", "elicitation/create"])]))

write_figure(SLUG, "choose-primitive.svg", figure(
    "choose",
    "どのprimitiveで公開するかの決め方",
    "処理や副作用があるならTool。ないなら、既存データの参照であればResource。"
    "それも違い、ユーザーが選ぶ対話手順ならPrompt。"
    "いずれにも当てはまらない場合は、要件と操作主体を再確認する。",
    [Section(
        nodes=[("start", "公開したい機能", "accent"),
               ("q1", "処理や副作用があるか", "decision"),
               ("tool", "Tool"), ("q2", "既存データの参照か", "decision"),
               ("res", "Resource"), ("q3", "ユーザーが選ぶ対話手順か", "decision"),
               ("prompt", "Prompt"), ("recheck", "要件と操作主体を再確認", "plain")],
        edges=[("start", "q1"),
               ("q1", "tool", "Yes"), ("q1", "q2", "No"),
               ("q2", "res", "Yes"), ("q2", "q3", "No"),
               ("q3", "prompt", "Yes"), ("q3", "recheck", "No")],
        layers=[["start"], ["q1"], ["tool", "q2"], ["res", "q3"],
                ["prompt", "recheck"]],
    )]))
