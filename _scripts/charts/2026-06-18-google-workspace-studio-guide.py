"""Google Workspace Studio記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-18-google-workspace-studio-guide"

write_figure(SLUG, "workflow-stages.svg", figure(
    "wsstages",
    "Workspace Studioのワークフローの3段",
    "Gmailの受信やSheetsの行追加、Formsの回答などがスターターとなり、"
    "Geminiが内容を読んで判断・分類・要約・生成を行い、"
    "Draft作成やSheetsへの書き込み、Chat通知、外部SaaS連携といったアクションで終わる。",
    [Section(
        nodes=[("start", "スターター（トリガー）\nGmail受信・Sheetsの行追加・Formsの回答など"),
               ("infer", "推論（Gemini）\n内容を読んで判断・分類・要約・生成", "accent"),
               ("act", "アクション（出力）\nDraft作成・Sheetsへの書き込み・"
                       "Chat通知・外部SaaS連携")],
        edges=[("start", "infer"), ("infer", "act")],
    )]))
