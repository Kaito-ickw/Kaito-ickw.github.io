"""Blender MCP×生成AIワークフロー記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-07-30-blender-mcp-3d-generation-workflow"

write_figure(SLUG, "blender-mcp-architecture.svg", figure(
    "arch",
    "Blender MCPの典型的な構成",
    "ユーザーの自然言語指示をMCPクライアントが受け取り、"
    "MCPプロトコル経由でBlender MCP Serverへ送る。"
    "ServerはローカルのソケットでBlender Add-onと通信し、"
    "Add-onがBlenderのPython API（bpy）を呼び出して"
    "モデル作成・編集・レンダリング・出力を行う。",
    [Section(
        nodes=[("user", "ユーザーの自然言語指示"),
               ("client", "MCPクライアント\n(Claude / Cursor / Codex等)", "accent"),
               ("server", "Blender MCP Server"),
               ("addon", "Blender Add-on"),
               ("bpy", "Blender Python API\n(bpy)", "plain"),
               ("out", "モデル作成・編集・\nレンダリング・出力")],
        edges=[("user", "client"), ("client", "server", "MCP"),
               ("server", "addon", "localhost / socket"),
               ("addon", "bpy"), ("bpy", "out")],
    )]))

write_figure(SLUG, "hybrid-iteration-loop.svg", figure(
    "loop",
    "生成→検査→修正→評価の反復ワークフロー",
    "3D仕様書をもとにGeneratorが初期メッシュを作り、"
    "InspectorがBlender内から寸法やメッシュ統計を検査する。"
    "ActorがBlender MCP経由で局所修正を行い、"
    "レンダリング結果をVisual Criticが要件と比較し、"
    "Validatorが用途別の機械的な合格条件を確認したうえで"
    "人間が最終承認する。問題があればGeneratorまたはActorへ戻る。",
    [Section(
        nodes=[("spec", "3D仕様書", "accent"),
               ("gen", "Generator\n初期メッシュ生成"),
               ("insp", "Inspector\n寸法・構造検査"),
               ("actor", "Actor\nBlender MCPで修正"),
               ("render", "レンダリング"),
               ("critic", "Visual Critic\n要件と画像を比較"),
               ("valid", "Validator\n用途別の機械検査"),
               ("human", "人間の最終承認", "cool")],
        edges=[("spec", "gen"), ("gen", "insp"), ("insp", "actor"),
               ("actor", "render"), ("render", "critic"),
               ("critic", "valid"), ("valid", "human"),
               ("critic", "actor", "問題あり", "dashed"),
               ("valid", "gen", "要件未達", "dashed")],
    )]))
