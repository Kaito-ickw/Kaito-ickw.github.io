"""ローカルとリモートのtransportの記事の図。sequenceDiagramはMermaidのまま残す。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-22-mcp-local-remote-transports"

write_figure(SLUG, "design-axes.svg", figure(
    "axes",
    "ローカルとリモートを分ける4つの軸",
    "Serverをどこで動かすかは同じ端末か別ホストかに分かれる。"
    "Clientとどう通信するかはstdioかStreamable HTTPか。"
    "誰が起動・停止するかはClientの子プロセスか独立サービスか。"
    "誰の権限で実行するかは端末ユーザーの権限かサービス用権限か。",
    [Section(title="Serverをどこで動かすか", framed=True,
             chips=["同じ端末", "別ホスト / クラウド"]),
     Section(title="Clientとどう通信するか", framed=True,
             chips=["stdio", "Streamable HTTP"]),
     Section(title="誰が起動・停止するか", framed=True,
             chips=["Clientが子プロセス起動", "独立サービスとして運用"]),
     Section(title="誰の権限で実行するか", framed=True,
             chips=["端末ユーザーの権限", "サービス用権限"])]))

write_figure(SLUG, "stdio-topology.svg", figure(
    "stdiotop",
    "stdioでつなぐときの構成",
    "MCP HostがMCP Clientを持ち、ClientがServerを子プロセスとして起動・停止する。"
    "Clientはstdinへ書き、Serverはstdoutで返す。"
    "Server子プロセスの先にローカルのToolやデータがある。",
    [Section(
        nodes=[("host", "MCP Host", "accent"), ("client", "MCP Client"),
               ("proc", "Server子プロセス"), ("tool", "ローカルTool / Data")],
        edges=[("host", "client"),
               ("client", "proc", "起動・停止 / stdin"),
               ("proc", "client", "stdout"),
               ("proc", "tool")],
    )]))

write_figure(SLUG, "session-lifecycle.svg", figure(
    "session",
    "MCP-Session-Idの寿命",
    "initializeでMCP-Session-Idを受け取り、後続のPOSTとGETで使う。"
    "DELETEかServer側の終了でセッションが終わる。"
    "セッションが失われると404 Not Foundが返り、新しいinitializeからやり直す。",
    [Section(
        nodes=[("init", "initialize", "accent"), ("sid", "MCP-Session-Idを受領"),
               ("req", "後続のPOST / GET"),
               ("end", "DELETEまたはServer側で終了"),
               ("missing", "404 Not Found", "warm"), ("reinit", "新しいinitialize")],
        edges=[("init", "sid"), ("sid", "req"), ("req", "end"),
               ("req", "missing"), ("missing", "reinit")],
        layers=[["init"], ["sid"], ["req"], ["end", "missing"], ["reinit"]],
    )]))

write_figure(SLUG, "trust-boundaries.svg", figure(
    "trust",
    "stdioとStreamable HTTPで信頼の境界が変わる",
    "stdioでは、Host / Clientと環境・OSの資格情報がそのままServer子プロセスへ渡る。"
    "Streamable HTTPでは、MCP ClientがAuthorization Serverと認可をやり取りし、"
    "取得したBearer tokenでMCP Resource Serverへアクセスする。",
    [Section(title="stdio", framed=True,
             nodes=[("host", "Host / Client", "accent"),
                    ("env", "環境・OSの資格情報"),
                    ("srv", "Server子プロセス")],
             edges=[("host", "srv"), ("env", "srv")],
             layers=[["host", "env"], ["srv"]]),
     Section(title="Streamable HTTP", framed=True,
             nodes=[("cli", "MCP Client", "accent"),
                    ("auth", "Authorization Server"),
                    ("res", "MCP Resource Server")],
             edges=[("cli", "auth", "認可", "both"),
                    ("cli", "res", "Bearer token")],
             # AuthとResourceを縦に積むと Client→Resource が層を飛び越して
             # 右へ迂回する。横に並べて2本とも1段の辺にする。
             layers=[["cli"], ["auth", "res"]])]))
