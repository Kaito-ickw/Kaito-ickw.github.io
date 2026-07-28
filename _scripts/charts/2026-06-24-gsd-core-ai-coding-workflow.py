"""GSD Core記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-24-gsd-core-ai-coding-workflow"

write_figure(SLUG, "phases.svg", figure(
    "gsdphase",
    "GSDの5つのphaseと戻り",
    "Discussで実装上の判断を決め、Planで調査してタスクへ分解し、Executeで計画単位に実装する。"
    "Verifyで要件と動作を確認し、不具合があればPlanへ戻る。"
    "合格すればShipでPull Requestを作り、次のphaseのDiscussへ入る。",
    [Section(
        nodes=[("discuss", "Discuss\n実装上の判断を決める", "accent"),
               ("plan", "Plan\n調査してタスクへ分解する"),
               ("execute", "Execute\n計画単位で実装する"),
               ("verify", "Verify\n要件と動作を確認する", "decision"),
               ("ship", "Ship\nPull Requestを作る"),
               ("next", "次のphase", "plain")],
        edges=[("discuss", "plan"), ("plan", "execute"), ("execute", "verify"),
               ("verify", "plan", "不具合あり"), ("verify", "ship", "合格"),
               ("ship", "next"), ("next", "discuss")],
    )]))

write_figure(SLUG, "agent-roles.svg", figure(
    "gsdroles",
    "オーケストレーターと4つのサブエージェント",
    "ユーザーがGSDコマンドを打つと、オーケストレーターが状態を確認して処理を振り分け、"
    "researcher・planner・executor・verifierのいずれかを動かす。"
    "調査と計画の成果は.planning/へ書かれ、executorがそれを読んでソースコードとGitを変更し、"
    "verifierが結果を.planning/へ書き戻す。",
    [Section(
        nodes=[("user", "ユーザー"), ("cmd", "GSDコマンド"),
               ("orch", "オーケストレーター\n状態確認と処理の振り分け", "accent")],
        edges=[("user", "cmd"), ("cmd", "orch")],
    ),
     Section(title="振り分け先のサブエージェント", framed=True,
             chips=["researcher", "planner", "executor", "verifier"]),
     Section(title="成果物の流れ", framed=True,
             nodes=[("rp", "researcher / planner"), ("planning", ".planning/", "accent"),
                    ("exec", "executor"), ("repo", "ソースコードとGit"),
                    ("verify", "verifier")],
             edges=[("rp", "planning"), ("planning", "exec"), ("exec", "repo"),
                    ("repo", "verify"), ("verify", "planning")])]))
