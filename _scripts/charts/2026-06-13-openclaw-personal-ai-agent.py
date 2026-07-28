"""OpenClaw記事の構成図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-13-openclaw-personal-ai-agent"

write_figure(SLUG, "architecture.svg", figure(
    "openclaw",
    "OpenClawの構成",
    "Telegram・Slack・Discord・WebChatからの入力をOpenClaw Gatewayが受け、"
    "LLM providerとTools / Nodesへ振り分ける。"
    "Gatewayはチャネルのルーティング、セッション管理、エージェント実行、"
    "ToolとSkillのポリシー、cronとイベントの処理を担う。"
    "Tools / Nodesの先には、ファイル・シェル・ブラウザ・検索・スマートフォンやPCがある。",
    [Section(
        nodes=[("ch", "Telegram / Slack / Discord / WebChat"),
               ("gw", "OpenClaw Gateway", "accent"),
               ("llm", "LLM provider"), ("tools", "Tools / Nodes")],
        edges=[("ch", "gw"), ("gw", "llm"), ("gw", "tools")],
    ),
     Section(
        title="Gateway が担う役割",
        framed=True,
        chips=["Channel routing", "Session management", "Agent runtime",
               "Tool / Skill policies", "Cron / event handling"],
        chip_style="plain",
    ),
     Section(
        title="Tools / Nodes が呼び出す先",
        framed=True,
        chips=["Files", "Shell", "Browser", "Search", "Phone / PC"],
    )]))
