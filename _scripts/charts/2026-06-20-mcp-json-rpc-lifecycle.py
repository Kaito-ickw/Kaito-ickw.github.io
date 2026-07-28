"""JSON-RPCとライフサイクルの記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-20-mcp-json-rpc-lifecycle"

write_figure(SLUG, "lifecycle.svg", figure(
    "lifecycle",
    "接続から終了までのライフサイクル",
    "ClientがServerへ接続し、initializeのrequestとresponse、"
    "notifications/initializedを経て、tools/listでTool定義を受け取る。"
    "Hostが定義をモデルへ渡し、必要なら承認を挟んでtools/callを送り、"
    "Tool結果をモデルへ渡したあとtransportを終了する。",
    [Section(steps=[
        "ClientがServerへ接続",
        "initialize request",
        "initialize response",
        "notifications/initialized",
        "tools/list request",
        "Tool定義を返す",
        "Hostが定義をモデルへ渡す",
        "必要ならユーザーが承認",
        "tools/call request",
        "Tool結果を返す",
        "Hostが結果をモデルへ渡す",
        "transportを終了",
    ])]))

write_figure(SLUG, "result-branches.svg", figure(
    "results",
    "tools/callの結果が3つに分かれる",
    "initializeからversionとcapabilityの確認、notifications/initialized、"
    "tools/listでの発見を経てtools/callを実行する。"
    "結果は、成功のresult、プロトコルの問題を示すJSON-RPC error、"
    "Tool処理の失敗を示すresultとisErrorの3つに分かれる。",
    [Section(
        nodes=[("init", "initialize", "accent"), ("cap", "versionとcapabilityを確認"),
               ("ready", "notifications/initialized"), ("list", "tools/listで発見"),
               ("call", "tools/callで実行"), ("q", "結果", "decision"),
               ("ok", "result", "cool"), ("err", "JSON-RPC error", "warm"),
               ("iserr", "result + isError", "warm")],
        edges=[("init", "cap"), ("cap", "ready"), ("ready", "list"),
               ("list", "call"), ("call", "q"),
               ("q", "ok", "成功"), ("q", "err", "プロトコル"), ("q", "iserr", "Tool失敗")],
        layers=[["init"], ["cap"], ["ready"], ["list"], ["call"], ["q"],
                ["ok", "err", "iserr"]],
    )]))
