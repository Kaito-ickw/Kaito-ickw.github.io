"""GraphAI記事の最小グラフ。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-16-graphai-agent-workflow-engine"

write_figure(SLUG, "minimal-graph.svg", figure(
    "graphai",
    "GraphAIの最小構成",
    "llmノードがopenAIAgentで生成し、その結果をoutputノードのcopyAgentが受け取る、"
    "2ノードだけのグラフ。",
    [Section(
        nodes=[("llm", "llm\nopenAIAgent", "accent"), ("out", "output\ncopyAgent")],
        edges=[("llm", "out")],
    )]))
