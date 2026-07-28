"""PythonでMCP Serverを作る記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-21-build-mcp-server-python"

write_figure(SLUG, "server-structure.svg", figure(
    "pysrv",
    "作るMCP Serverの位置",
    "ユーザーの操作はMCP Hostが受け、MCP Clientがstdio上のJSON-RPCで"
    "Python製のMCP Serverと通信する。Serverはlist_notesとread_noteの2つのToolを公開し、"
    "どちらもnotesディレクトリのMarkdownを読む。",
    [Section(
        nodes=[("user", "ユーザー"), ("host", "MCP Host"), ("client", "MCP Client"),
               ("server", "Python MCP Server", "accent"),
               ("list", "list_notes"), ("read", "read_note"),
               ("notes", "notes/*.md")],
        edges=[("user", "host"), ("host", "client"),
               ("client", "server", "stdio / JSON-RPC"),
               ("server", "list"), ("server", "read"),
               ("list", "notes"), ("read", "notes")],
    )]))

write_figure(SLUG, "stdio-streams.svg", figure(
    "stdio",
    "stdoutとstderrの使い分け",
    "MCP ClientはJSON-RPCをserverのstdinへ書き込む。"
    "server.pyはstdoutにはJSON-RPCだけを出し、診断ログはstderrへ出す。"
    "stdoutをClientが読み、stderrはログの表示・収集にまわる。"
    "stdoutにログを混ぜるとJSON-RPCが壊れる。",
    [Section(
        nodes=[("client", "MCP Client", "accent"), ("stdin", "server stdin"),
               ("py", "server.py"), ("stdout", "server stdout"),
               ("stderr", "server stderr"), ("logs", "ログ表示・収集")],
        edges=[("client", "stdin", "JSON-RPC"), ("stdin", "py"),
               ("py", "stdout", "JSON-RPCのみ"), ("py", "stderr", "診断ログ"),
               ("stdout", "client"), ("stderr", "logs")],
        layers=[["client"], ["stdin"], ["py"], ["stdout", "stderr"], ["logs"]],
    )]))
