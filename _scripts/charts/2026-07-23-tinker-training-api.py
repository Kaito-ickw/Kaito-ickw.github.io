"""Tinker記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-07-23-tinker-training-api"

write_figure(SLUG, "training-loop.svg", figure(
    "tinker",
    "運用ログを学習へ回すループ",
    "エージェントがIssueやタスクを処理し、テスト結果・レビュー・人間評価を記録する。"
    "成功と失敗を報酬または教師データへ変換し、TinkerでSFT・DPO・RLを実行して"
    "学習済み重みを再配置する。同じ評価セットで改善を検証し、"
    "改善が確認できれば運用へ戻し、悪化や変化なしならデータと報酬設計を見直す。",
    [Section(
        nodes=[("run", "エージェントがIssue/タスクを処理", "accent"),
               ("log", "テスト結果・レビュー・人間評価を記録"),
               ("conv", "成功/失敗を報酬または教師データへ変換"),
               ("train", "TinkerでSFT・DPO・RLを実行"),
               ("deploy", "学習済み重みを再配置"),
               ("eval", "同じ評価セットで改善を検証", "decision"),
               ("review", "データ・報酬設計を見直す", "warm")],
        edges=[("run", "log"), ("log", "conv"), ("conv", "train"),
               ("train", "deploy"), ("deploy", "eval"),
               ("eval", "run", "改善を確認"),
               ("eval", "review", "悪化・変化なし"), ("review", "conv")],
    )]))
