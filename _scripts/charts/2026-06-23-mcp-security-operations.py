"""MCPのセキュリティと運用の記事の図。認可のsequenceDiagramはMermaidのまま残す。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-23-mcp-security-operations"

write_figure(SLUG, "data-flow.svg", figure(
    "secflow",
    "外部から来た文字列がモデルへ届くまで",
    "ユーザーの操作はMCP HostからMCP Client、MCP Serverを経て外部API・DB・ファイルへ届く。"
    "逆向きに、Tool結果やResource、外部文書がServerへ入り、Clientを通じてモデルへ返る。"
    "この戻りの経路に外部が書いた文字列が乗るため、指示として解釈させない扱いが要る。",
    # 往路と復路を1本の鎖に詰めると、戻りの辺が2本とも右へ迂回して読めなくなる。
    # 記事の論点は復路に外部由来の文字列が乗ることなので、経路ごとに分ける。
    [Section(title="依頼が下る経路", framed=True,
             nodes=[("user", "ユーザー"), ("host", "MCP Host / AIアプリ", "accent"),
                    ("client", "MCP Client"), ("server", "MCP Server"),
                    ("api", "外部API / DB / ファイル")],
             edges=[("user", "host"), ("host", "client"), ("client", "server"),
                    ("server", "api")]),
     Section(title="結果が戻る経路", framed=True,
             nodes=[("api2", "外部API / DB / ファイル"),
                    ("data", "Tool結果・Resource・外部文書", "warm"),
                    ("server2", "MCP Server"), ("client2", "MCP Client"),
                    ("model", "モデルへの入力", "accent")],
             edges=[("api2", "data"), ("data", "server2"), ("server2", "client2"),
                    ("client2", "model")])]))
