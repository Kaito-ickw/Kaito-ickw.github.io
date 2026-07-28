"""MCP概要記事の図。日本語版と英語版の両方を出力する。"""
from diagram import Section, figure, sequence, write_figure

JA = "2026-06-17-mcp-protocol-overview"
EN = "2026-06-17-mcp-protocol-overview-en"

# ---------------------------------------------------------------- 全体像
write_figure(JA, "mcp-overview.svg", figure(
    "mcpov",
    "MCPが標準化している範囲",
    "ユーザーの操作はAIアプリケーション（MCP Host）が受け取り、"
    "MCP Clientを通じてMCP Serverと双方向に通信する。この通信をMCPが標準化している。"
    "Serverの先には既存API・データベース・ローカルファイルがある。HostはLLMも呼び出す。",
    [Section(
        nodes=[("user", "ユーザー"), ("host", "AIアプリケーション\nMCP Host", "accent"),
               ("llm", "LLM", "plain"), ("client", "MCP Client"),
               ("server", "MCP Server", "accent"),
               ("api", "既存API"), ("db", "データベース"), ("files", "ローカルファイル")],
        edges=[("user", "host"), ("host", "llm", "", "dashed"), ("host", "client"),
               ("client", "server", "MCPで標準化された通信", "both"),
               ("server", "api"), ("server", "db"), ("server", "files")],
        layers=[["user"], ["host"], ["client", "llm"], ["server"],
                ["api", "db", "files"]],
    )]))

write_figure(EN, "mcp-overview-en.svg", figure(
    "mcpov",
    "What MCP standardizes",
    "The user talks to an AI application acting as the MCP Host, which reaches an "
    "MCP Server through an MCP Client. That connection is what MCP standardizes. "
    "Behind the server sit an existing API, a database and local files. "
    "The host also calls an LLM.",
    [Section(
        nodes=[("user", "User"), ("host", "AI application\nMCP Host", "accent"),
               ("llm", "LLM", "plain"), ("client", "MCP Client"),
               ("server", "MCP Server", "accent"),
               ("api", "Existing API"), ("db", "Database"), ("files", "Local files")],
        edges=[("user", "host"), ("host", "llm", "", "dashed"), ("host", "client"),
               ("client", "server", "Standardized by MCP", "both"),
               ("server", "api"), ("server", "db"), ("server", "files")],
        layers=[["user"], ["host"], ["client", "llm"], ["server"],
                ["api", "db", "files"]],
    )]))

# ---------------------------------------------------------------- Tool呼び出し
write_figure(JA, "tool-call-flow.svg", sequence(
    "mcptool",
    "Tool呼び出しで3者がやり取りする順",
    "MCP ServerがHostへtools/listでTool定義を渡し、HostがそれをLLMへ渡す。"
    "LLMがTool使用を提案するとHostがServerへtools/callを送り、"
    "返ってきたTool結果をHostがLLMへ渡す。",
    ["MCP Server", "MCP Host", "LLM"],
    [("MCP Server", "MCP Host", "tools/list", False),
     ("MCP Host", "LLM", "Tool定義を渡す", False),
     ("LLM", "MCP Host", "Tool使用を提案", True),
     ("MCP Host", "MCP Server", "tools/call", False),
     ("MCP Server", "MCP Host", "Tool結果", True),
     ("MCP Host", "LLM", "結果を渡す", False)]))

write_figure(EN, "tool-call-flow-en.svg", sequence(
    "mcptool",
    "How the three parties exchange a tool call",
    "The MCP Server hands tool definitions to the Host through tools/list, and the "
    "Host makes them available to the LLM. When the LLM proposes a tool use, the "
    "Host sends tools/call to the server and passes the returned result back.",
    ["MCP Server", "MCP Host", "LLM"],
    [("MCP Server", "MCP Host", "tools/list", False),
     ("MCP Host", "LLM", "Expose definitions", False),
     ("LLM", "MCP Host", "Propose tool use", True),
     ("MCP Host", "MCP Server", "tools/call", False),
     ("MCP Server", "MCP Host", "Tool result", True),
     ("MCP Host", "LLM", "Pass the result", False)]))
