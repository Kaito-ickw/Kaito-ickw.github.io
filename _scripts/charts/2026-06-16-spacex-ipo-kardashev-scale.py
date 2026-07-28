"""カルダシェフ・スケールの段階。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-16-spacex-ipo-kardashev-scale"

write_figure(SLUG, "kardashev-scale.svg", figure(
    "kardashev",
    "カルダシェフ・スケールの3段階",
    "Type Iは惑星に届く太陽エネルギーを使い切る段階、"
    "Type IIは恒星のエネルギーを丸ごと使う段階、"
    "Type IIIは銀河系規模のエネルギーを使う段階。",
    [Section(
        nodes=[("t1", "Type I\n惑星に届く太陽エネルギーを使い切る", "accent"),
               ("t2", "Type II\n恒星のエネルギーを丸ごと使う"),
               ("t3", "Type III\n銀河系規模のエネルギーを使う")],
        edges=[("t1", "t2"), ("t2", "t3")],
    )]))
