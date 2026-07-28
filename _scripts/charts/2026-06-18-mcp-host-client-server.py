"""Host / Client / Server の役割分担の記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-18-mcp-host-client-server"

write_figure(SLUG, "host-client-server.svg", figure(
    "hcs",
    "1つのHostが複数のServerを持つときの構成",
    "MCP HostはLLMと、Serverごとに1つずつのMCP Clientを持つ。"
    "Client AはファイルシステムをServer A経由で、"
    "Client BはGitHubなどの外部APIをServer B経由で扱う。"
    "ClientとServerは1対1の専用接続で結ばれる。",
    [Section(
        nodes=[("user", "ユーザー"), ("host", "MCP Host\nAIアプリケーション", "accent"),
               ("llm", "LLM", "plain"), ("ca", "MCP Client A"), ("cb", "MCP Client B"),
               ("sa", "MCP Server A\nファイル操作"), ("sb", "MCP Server B\nIssue操作"),
               ("files", "ファイルシステム"), ("api", "外部API")],
        edges=[("user", "host"), ("host", "llm", "", "dashed"),
               ("host", "ca"), ("host", "cb"),
               ("ca", "sa", "専用の接続", "both"), ("cb", "sb", "専用の接続", "both"),
               ("sa", "files"), ("sb", "api")],
        # LLMを単独の層に置くと横幅いっぱいの箱になり、Hostから各Clientへの辺が
        # それを避けて左右へ迂回する。Hostの隣に置いて横向きの辺で結ぶ。
        layers=[["user"], ["host", "llm"], ["ca", "cb"], ["sa", "sb"],
                ["files", "api"]],
    )]))

write_figure(SLUG, "connection-sequence.svg", figure(
    "hcsseq",
    "接続からTool実行までの11段",
    "ClientがServerへinitializeを送り、VersionとCapabilityを合意し、"
    "tools/listでTool定義を取得する。HostがTool定義を管理し、"
    "ユーザーの依頼を受けてLLMとHostがTool使用を決め、必要なら承認を挟んでtools/callを送る。"
    "Serverが処理して返したTool結果を、HostがLLMへ渡して回答を作る。",
    [Section(steps=[
        "ClientがServerへinitialize",
        "VersionとCapabilityを合意",
        "Clientがtools/listを取得",
        "HostがTool定義を管理",
        "ユーザーが依頼",
        "LLMとHostがTool使用を決定",
        "必要ならユーザーが承認",
        "Clientがtools/callを送信",
        "Serverが処理・外部APIを実行",
        "Tool結果をClientへ返す",
        "Hostが結果をLLMへ渡し回答",
    ])]))
