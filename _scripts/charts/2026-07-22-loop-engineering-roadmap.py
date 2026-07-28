"""Loop Engineering記事の図。日本語版と英語版の両方を出力する。"""
from diagram import Section, figure, write_figure

JA = "2026-07-22-loop-engineering-roadmap"
EN = "2026-07-22-loop-engineering-roadmap-en"

write_figure(JA, "loop-structure.svg", figure(
    "loopja",
    "自律ループの骨格",
    "時刻やイベントを起動条件として作業を取得し、エージェントが実行する。"
    "機械的な検証に失敗したら原因と状態を記録して実行へ戻る。"
    "合格したら人間の承認を経て状態を保存し、停止条件を見て継続か終了かを決める。",
    [Section(
        nodes=[("trigger", "起動条件\n時刻・イベント", "accent"),
               ("fetch", "作業を取得"), ("exec", "エージェントが実行"),
               ("gate", "機械的な検証", "decision"),
               ("retry", "原因と状態を記録", "warm"),
               ("approve", "人間の承認"), ("state", "状態を保存"),
               ("stop", "停止条件", "decision"), ("end", "完了", "cool")],
        edges=[("trigger", "fetch"), ("fetch", "exec"), ("exec", "gate"),
               ("gate", "retry", "失敗"), ("retry", "exec"),
               ("gate", "approve", "合格"), ("approve", "state"), ("state", "stop"),
               ("stop", "fetch", "継続"), ("stop", "end", "終了")],
        layers=[["trigger"], ["fetch"], ["exec"], ["gate"], ["retry", "approve"],
                ["state"], ["stop"], ["end"]],
    )]))

write_figure(EN, "loop-structure-en.svg", figure(
    "loopen",
    "The skeleton of an autonomous loop",
    "A time or event trigger fetches work and an agent executes it. If mechanical "
    "verification fails, the cause and state are recorded and execution is retried. "
    "On pass, a human approves, state is saved, and the stopping condition decides "
    "whether to continue or finish.",
    [Section(
        nodes=[("trigger", "Trigger\ntime / event", "accent"),
               ("fetch", "Fetch work"), ("exec", "Agent executes"),
               ("gate", "Mechanical verification", "decision"),
               ("retry", "Record cause and state", "warm"),
               ("approve", "Human approval"), ("state", "Save state"),
               ("stop", "Stopping condition", "decision"), ("end", "Done", "cool")],
        edges=[("trigger", "fetch"), ("fetch", "exec"), ("exec", "gate"),
               ("gate", "retry", "Fail"), ("retry", "exec"),
               ("gate", "approve", "Pass"), ("approve", "state"), ("state", "stop"),
               ("stop", "fetch", "Continue"), ("stop", "end", "End")],
        layers=[["trigger"], ["fetch"], ["exec"], ["gate"], ["retry", "approve"],
                ["state"], ["stop"], ["end"]],
    )]))
