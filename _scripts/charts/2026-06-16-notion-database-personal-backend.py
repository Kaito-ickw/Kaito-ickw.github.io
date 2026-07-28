"""Notionをバックエンドにする記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-16-notion-database-personal-backend"

write_figure(SLUG, "data-model.svg", figure(
    "notionmodel",
    "Notionデータベースの構造",
    "データベースはコンテナであり、その中のデータソースが表そのものにあたる。"
    "データソースは、1行のレコードにあたるページと、カラムにあたるプロパティを持つ。",
    [Section(
        nodes=[("db", "データベース（コンテナ）"),
               ("ds", "データソース（表そのもの）", "accent"),
               ("page", "ページ = 1行のレコード"), ("prop", "プロパティ = カラム")],
        edges=[("db", "ds"), ("ds", "page"), ("ds", "prop")],
    )]))

write_figure(SLUG, "access-paths.svg", figure(
    "notionaccess",
    "Notionデータソースへの2つの入口",
    "自作アプリやエージェントはAPI経由で、人はNotionの画面から、"
    "同じデータソースを読み書きする。データソースの内容はアプリ側へも返る。",
    [Section(
        nodes=[("app", "自作アプリ / エージェント", "accent"),
               ("gui", "Notion の画面（人が操作）"),
               ("ds", "Notion データソース")],
        edges=[("app", "ds"), ("gui", "ds"), ("ds", "app")],
        layers=[["app", "gui"], ["ds"]],
    )]))
