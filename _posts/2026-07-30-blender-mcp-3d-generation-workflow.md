---
layout: post
title: "生成AIとBlender MCPで、3D未経験者はどこまでモデルを作れるか"
subtitle: Text-to-3DとBlender操作エージェントの役割を分けて考える
categories: AI開発
tags: ["Blender", "MCP", "AIエージェント", "3Dモデリング", "AI", "AIセーフティ"]
lang: ja
last_modified_at: 2026-08-02
---

3DモデリングをやったことがなくてもBlender MCPを使えば実用的なモデルが作れる、という話をよく見かけるようになった。テキストや画像から一発でモデルを生成するサービスと、LLMがBlenderを操作するエージェントは、どちらも「AIで3Dを作る」とまとめて語られがちだが、できることの中身はかなり違う。

この記事では両者を区別したうえで、現在の生成AIが得意なこと・苦手なことを整理し、単体利用で起きやすい失敗と、それを減らすための反復ワークフローの設計案をまとめる。後半では、そのうちBlender MCP単体で作る方式を実際に動かし、何回直せば要件を満たせたかを記録した。Image-to-3Dを絡めた検証は未実施で、進め方だけを残している。

## 生成AIで3D制作は本当に簡単になったのか

「プロンプト一発でゲーム用アセットが完成した」というデモ動画は数多くある。ただし、そうしたデモの多くは見た目が整った静止画やターンテーブル動画で完結しており、そのモデルをゲームエンジンへ入れて動かす、3Dプリンタで出力する、CADとして寸法通りに編集するといった後工程まで通しているケースは少ない。

生成AIが担えるようになったのは「初期案を素早く作る」工程であって、「作ったものを目的に合わせて検査し、直す」工程が消えたわけではない。この記事では、3D未経験者が実際にぶつかる壁を、ツールの分類・Blender MCPの仕組み・現状の得意不得意・反復ワークフローの4段階に分けて整理する。

## Text-to-3D、Image-to-3D、Blender操作エージェントの違い

「AIで3Dを作る」という言葉は、少なくとも次の4つを指しうる。

1. **Text-to-3D / Image-to-3D**（Meshy、Tripo、Hunyuan3D、Hyper3D Rodinなど）: テキストや参照画像から、メッシュ・テクスチャ・PBR素材を直接生成する
2. **Blender操作エージェント**（Blender MCPなど）: Claude / Cursor / CodexなどからBlenderを自然言語操作し、Blenderの`bpy`を通じてオブジェクト作成・配置・マテリアル設定・レンダリング・エクスポートを行う
3. **LLMによる`bpy`コード生成**: MCPを介さず、LLMが`bpy`スクリプトを直接書いて実行する方式。手軽だが、構文エラー、Blenderの状態依存、形状の不整合が起きやすい
4. **補助AI**: 参照画像生成、AIテクスチャリング、リメッシュ・リトポロジー・リギング・アニメーション、VLMによるレンダリング画像の評価

1は「モデルを直接生成するAI」、2と3は「Blender内の作業を代行するエージェント」にあたる。この2つを同じ土俵で比較すると、「Text-to-3Dの方が速い」「Blender MCPの方が精密」といった単純な優劣に見えてしまうが、実際は生成物の性質が異なる。1は完成形に近い1オブジェクトの塊を出す一方、2と3はBlenderのシーングラフに乗った、後から個別に触れる部品の集まりを作る。この違いが、後述する用途別の向き不向きに直結する。

## Blender MCPの構成とできること

Blender MCPの実装として広く使われているのは`ahujasid/blender-mcp`で、MITライセンスのオープンソースプロジェクトである。典型的な構成は次のようになる。

![ユーザーの自然言語指示がMCPクライアントからBlender MCP Serverへ送られ、ローカルソケット経由でBlender Add-onがbpyを呼び出す構成図](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/blender-mcp-architecture.svg){: .chart}

MCPクライアント（Claude Desktop、Cursor、Codexなど）がBlender MCP Serverへ接続し、ServerはローカルのソケットでBlender側のAdd-onと通信する。Add-onがBlenderのPython API（`bpy`）を呼び出すことで、実際のシーン操作が行われる。

### 実際に確認できる機能とREADME記載のみの機能を分ける

`ahujasid/blender-mcp`のREADMEには多くの機能が書かれている。後述する検証（Blender 4.5.9 LTS + addon v1.2 / MCP Server 1.3.0、2026年8月2日実施）で自分の手元を通ったものと、通していないものを分けると次のようになる。

- **実際に動かせたもの**: シーン情報の取得（`get_scene_info`）、オブジェクト情報の取得（`get_object_info`）、任意Pythonコードの実行（`execute_blender_code`）。オブジェクトの作成・変形、マテリアル設定、ライト・カメラ設定、Cyclesでのレンダリング、`.blend`保存、GLB / FBX / STLへのエクスポートは、いずれも`execute_blender_code`経由で実行できた
- **この環境では動かなかったもの**: ビューポートのスクリーンショット取得（`get_viewport_screenshot`）。GUIの3Dビューが必要で、ヘッドレス実行では`bpy.ops.screen.screenshot_area.poll() failed`となる
- **README記載だが未検証**: Poly Havenからのアセット取得、Sketchfabモデルの検索・取り込み、Hyper3D Rodinによる生成モデルの取り込み、Hunyuan3Dとの連携、リモートホストでの利用

注意しておきたいのは、「モデルを作る」操作の実体がほぼすべて`execute_blender_code`だという点である。プリミティブ追加やマテリアル設定に対応する専用ツールがあるわけではなく、LLMが書いた`bpy`スクリプトがそのままBlenderへ渡る。後述の安全性の話は付随的な注意ではなく、この構成そのものの話になる。

### 2026年のAnthropic公式Blender連携

2026年4月28日、AnthropicはClaudeを創作ツールと直接連携させる「Claude for Creative Work」を発表した。Adobe、Autodesk Fusion、Ableton、SketchUp、Affinity by Canva、Resolume Arena/Wire、Splice、そしてBlenderの9つのコネクタが対象で、公式発表では「Blenderの開発者自身がこのMCPコネクタを作成し、Claude向けに公式提供している」と説明されている。MCPベースであるため、Claude以外のLLMからも利用できる設計になっている。

一方でこの発表の数日後、AnthropicがBlender Development Fundへ年間240,000ユーロ規模のCorporate Patronとして参加したことがコミュニティで議論を呼び、Blender Foundationは2026年5月4日に、この関係を継続的なパトロネージではなく一回限りの寄付へ引き下げたと発表した。Blender側は「生成AI機能を現在Blenderへ組み込む予定はない」という立場も改めて示している。公式コネクタの提供と、Blender本体への生成AI機能の統合は別の話として扱われている点に注意したい。

## 任意コード実行のリスクとローカル限定運用

Blender MCPの`execute_blender_code`に代表される「任意のPythonコードを実行できる」機能は、複雑な操作を柔軟に行える一方で、独立した注意が必要な機能でもある。

一般的なリスクとして、次のようなものが挙げられる。

- Blenderが読み込むシーンデータ、外部アセットの説明文、Web上のドキュメントなどにモデルへの指示が紛れ込む、プロンプトインジェクションの余地がある
- 外部アセットのURLを受け取って取得する機能では、意図しない内部ネットワークやローカルリソースへのアクセス（SSRF）につながりうる
- 任意コード実行そのものが、ファイルの読み書きや外部通信を含む広い権限を持つ

対策として、次のような運用が現実的である。

- Blender MCP ServerをローカルホストのみでバインドしLAN・インターネットへ公開しない
- 実行前に生成されたコードやツール呼び出しの内容を人間が確認する
- 実行可能なモジュールやファイルパスを制限する「Safe Mode」的な実装を選ぶ（`djeada/blender-mcp-server`はこの方向で、スクリプトパスの許可リストや危険モジュールのimport制限を持つ）
- Blenderプロセス自体を、重要なファイルやクラウド資格情報にアクセスできない環境で動かす

この点は、以前書いた[MCPサーバーを安全に運用する]({% post_url 2026-06-23-mcp-security-operations %})で扱った「Toolを小さく設計する」「破壊的操作には二段階を用意する」という考え方がそのまま当てはまる。Blender MCPに限らず、任意コード実行を公開するMCP Serverでは、便利さと引き換えに何を検査・確認すべきかを個別に設計する必要がある。

## 主要ツール比較

Text-to-3D / Image-to-3Dの主要ツールを、2026年7月時点の公開情報で比較する。料金・ライセンスは変わりやすいため、利用前に必ず公式ページで確認してほしい。

| ツール | 無料枠 | 有料プラン（月額目安） | ライセンス・商用利用の注意 |
| :--- | :--- | :--- | :--- |
| Meshy | 100 credit/月 | Pro $20〜、Studio $60〜 | 無料プランの出力はCC BY 4.0（表示すれば商用利用可） |
| Tripo | 300 credit/月 | Professional 約$15.9〜、Max/Team上位プランあり | 無料プランは商用利用不可、生成モデルの利用条件をプランごとに確認する必要あり |
| Hunyuan3D 2.1 | オープンウェイト（自己ホスト） | ─（自己ホスティングのため課金なし） | 独自のCommunity License。EU・英国・韓国は利用対象外。月間アクティブユーザーが100万人を超える製品は別途商用ライセンスが必要 |
| Hyper3D Rodin | Free（$1.5/credit相当） | Business $120/月〜 | Blender MCP経由では試用枠つきで呼び出し可能 |

Hunyuan3D 2.1は、形状生成（DiT）とテクスチャ生成（Paint）を分離した構成を取っている点が特徴で、後述するハイブリッドワークフローの「初期形状だけを先に確定する」という考え方と相性がよい。ただし独自ライセンスの地域制限・商用利用の閾値は無視できないため、業務利用を検討する際は必ず原文を確認する。

## 現状の得意・不得意と用途別評価軸

得意なもの、苦手なものを分けると次のようになる。

**得意そうなもの**

- 単純なプロップ、小物、デフォルメ物体
- コンセプト検討やラフモデル
- 既存アセットの配置によるシーン構築
- マテリアル、照明、カメラ、レンダリング設定
- 寸法や構成が明確なプリミティブ中心のモデル
- 同じ処理の反復、バリエーション生成

**難しいもの**

- 厳密なトポロジー
- 可動部や接合部を含む機械設計
- 文字、ロゴ、細い部品
- 見えない背面や内部構造の推定
- 正確な寸法、公差、3Dプリント適性
- キャラクターの手指、顔、衣服、リギング
- 一貫した複数オブジェクトの位置関係

「見た目がそれらしい」ことと「編集・製造・ゲーム投入に耐える」ことの間には、まだ距離がある。この距離は用途によって幅が変わるため、一律に評価せず用途ごとに必要品質を分ける。

| 用途 | 主な評価軸 |
| :--- | :--- |
| コンセプト画像・静止画 | 見た目、構図、質感 |
| ゲーム背景・小物 | ポリゴン数、UV、PBR、LOD、衝突判定 |
| アニメーション | トポロジー、リグ、変形耐性 |
| 3Dプリント | watertight性、厚み、非多様体、寸法精度 |
| CAD・製造 | 寸法、公差、拘束条件、編集可能性 |

コンセプト画像なら一発生成でも十分なことが多い一方、3Dプリントや製造ではAIの見た目評価だけで安全性・強度・寸法精度を保証してはいけない。

## 生成→検査→修正→評価の反復ワークフロー

ここまでの整理を踏まえると、3D生成AIに完成品を一発生成させるより、初期メッシュをAIで作り、Blender MCPを通じて検査・修正・再レンダリングを繰り返す方が、3D未経験者でも実用水準へ近づけるのではないか、というのがこの記事の中心的な仮説になる。

![3D仕様書を起点に、Generator・Inspector・Actor・Visual Critic・Validatorの各役割が反復し、最後に人間が承認する流れを示した図](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/hybrid-iteration-loop.svg){: .chart}

役割を分けると次のようになる。

- **Generator**: 初期モデルを作る
- **Inspector**: 寸法、オブジェクト構成、メッシュ統計をBlender内から調べる
- **Actor**: Blender MCP経由で局所修正を行う
- **Visual Critic**: レンダリング画像と要件を比較する
- **Validator**: 用途別の合格条件を機械的に確認する

単一のエージェントへ長い指示を一度に渡すより、工程と評価基準を固定した反復にする方が再現性を上げられるのではないか、という考え方である。

### 仮説：画像を先に確定してからImage-to-3Dへ渡す

テキストから直接3D化すると、形状と意匠を同時に推論する必要がある。先に画像生成AIとの対話で正面・側面・背面のデザインを詰め、その画像をImage-to-3Dへ渡す方が、意図との一致度を上げやすいのではないか。Hunyuan3D 2.1のように形状生成とテクスチャ生成を分離した構成は、この段階分けとも相性がよい。

### 仮説：自然言語だけでなく「3D仕様書」を中間表現にする

生成・修正・評価の全工程で参照する正本として、次のようなYAML形式の仕様書を用意する案を検討する。

```yaml
asset:
  purpose: game_prop
  object: retro_vending_machine
  dimensions_m: [0.9, 0.8, 1.9]
  style: retro_futuristic
  required_parts:
    - display_window
    - payment_panel
    - product_buttons
    - rear_panel
  constraints:
    max_faces: 30000
    pbr: true
    separate_movable_parts: true
    readable_text: false
  outputs:
    - blend
    - glb
    - turntable_render
```

自然言語の指示だけに頼ると、GeneratorとActorとValidatorが微妙に異なる解釈をしてしまう場合がある。仕様書を固定の参照点にすることで、各役割が同じ基準で判断できるようにする狙いがある。

### 仮説：AIの自己評価を画像だけに依存させない

レンダリング画像のVLM評価に加えて、Blender内から取得できる機械的な指標を組み合わせる。

- bounding boxと指定寸法との差
- face / vertex数
- non-manifold edge、disconnected component
- 法線方向、UVの有無、マテリアル数
- オブジェクト名・部品数
- 原点・スケール・回転の適用状態
- 3Dプリント用途なら厚み・watertight性

「見た目の評価」と「構造評価」を分離しておくことで、Visual Criticが見落とす形状の破綻をValidatorが拾える可能性がある。

### 関連研究

この反復方式の方向性は、2026年に発表されたいくつかの研究とも重なる。

- **EZBlender**（arXiv:2601.07143、WACV 2026併催ワークショップでBest Paper受賞）は、計画によるタスク分解と局所的なReActを組み合わせ、編集品質を保ちながらレイテンシと計算コストを下げる方向を示している
- **From Idea to Co-Creation: A Planner-Actor-Critic Framework for Agent Augmented 3D Modeling**（arXiv:2601.05016、ACM CHI 2026 Extended Abstracts）は、Blender MCPを単発プロンプトで操作する方式に比べ、Planner / Actor / Critic、および人間の監督を組み合わせた反復方式の方が、誤りの減少とモデリング結果の複雑さ・品質向上につながったと報告している
- **Hunyuan3D 2.0**（arXiv:2501.12202）は、shape生成とtexture生成を分離した構成を採用しており、Image-to-3Dで初期形状を作りBlender側で構造・用途別の修正を行うという本記事の仮説と相性がよい

いずれも実在する論文だが、具体的な改善率などの数値は要旨レベルでの確認にとどまっており、数値を引用する場合は原論文の本文を別途確認する必要がある。

### Skill化候補

反復のたびにLLMへ全工程を考えさせるのではなく、成功した操作を固定のSkillとして持たせておくと、再現性・トークン効率・安全性の改善が見込める。候補としては次のようなものがある。

- `import_and_normalize_asset`
- `inspect_scene`
- `validate_mesh`
- `setup_product_render`
- `create_turntable_animation`
- `export_for_web`

このアイデアは、Claude Codeにおける[Skillsの仕組み]({% post_url 2026-06-10-claude-code-skills-guide %})と発想が近い。決まった手順をSkillとして固定し、モデルに毎回ゼロから考えさせないという点は、Blender操作にもそのまま応用できそうである。

## 検証の順序

比較する方式は多いが、一度にすべてを試すのではなく、差分が確認しやすい順に進める。

1. **D: Blender MCPのみ**（自然言語操作だけでどこまで作れるか）
2. **B: Image-to-3Dのみ**（生成AI単体の初期メッシュの質）
3. **E: Image-to-3D → Blender MCPによる反復修正**（DとBの組み合わせ）

以下ではDを実施した結果を書く。BとEは初期メッシュの生成源（Meshy / TripoのAPIキー、もしくはHunyuan3Dの自己ホスト環境）が要るため未実施で、この記事の末尾に進め方だけ残している。

## 検証D: Blender MCPだけで作る

### 実行環境

| 項目 | 内容 |
| :--- | :--- |
| 実施日 | 2026年8月2日 |
| Blender | 4.5.9 LTS（Linux x64、WSL2上） |
| Blender MCP | `ahujasid/blender-mcp` addon v1.2 / MCP Server 1.3.0 |
| MCPクライアント | 自作の最小stdioクライアント（Claude Code から JSON-RPC を直接叩く） |
| レンダラ | Cycles CPU、48サンプル、640×640 |
| 外部API | 未使用（Poly Haven / Sketchfab / Hyper3D / Hunyuan3Dはすべて無効） |

セットアップで引っかかった点を先に書いておく。

Add-onはBlenderのGUIを前提にしていて、`blender -b`（バックグラウンド）では明示的に起動を拒否する。コマンドを`bpy.app.timers`経由でメインスレッドへ渡す設計のため、イベントループが回らない環境では実行されないからである。手元のWSL2ではXvfb上のGUI起動が安定せず（EGLエラーでsegfault、起動できてもコマンドが返らない）、Add-onのコマンド処理（`execute_command`）はそのまま使いつつ、ソケット受信とディスパッチだけをメインスレッドのループへ置き換えるシムを書いて検証した。MCP Server側は無改変で、`uv run blender-mcp`をそのまま使っている。デスクトップでGUIを開いたまま使うぶんには不要な作業だが、CIやサーバー上で回そうとすると最初にぶつかる制約になる。

細かい挙動も2つ記録しておく。テレメトリは既定で有効（匿名の使用状況）で、`DISABLE_TELEMETRY=true`で無効化できる。またMCP Serverは接続確認としてツール呼び出しのたびに`get_polyhaven_status`をBlenderへ1回送る。今回の記録では、実際のツール実行25回に対して接続確認が34回発生していた。

### 課題1: ローポリの宝箱

要件を与えず「ローポリの宝箱を作って」から始めた。1回目の生成は`bpy`としては一発で通り、エラーもない。

![生成1回目のレンダリング。蓋の円柱が本体より大きく、宝箱ではなく樽か丸太に見える](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/chest-iteration-1.webp)

蓋に使った円柱が本体（0.6×0.4×0.3m）より大きく、全体としては樽になった。このとき数値検査は、蓋の寸法が0.8×0.8×1.2mであること、全体のバウンディングボックスが1.2×0.83×0.96mであること、最下点が床から0.04m浮いていることを機械的に返している。

ここから3回直して完成させた。

1. 蓋を`bmesh.ops.bisect_plane`で半分にしようとしたが効かず、円柱のまま
2. 円弧の頂点から半円柱を組み直して形状は解決。ただし金具と錠前が空中に浮いた
3. 原因は最初の生成にあった`bpy.ops.object.transform_apply(scale=True)`。この演算子は`location`と`rotation`も既定で`True`のため、位置がメッシュ側へ焼き込まれ、以降の`location`指定が二重にずれていた。原点をジオメトリ中心へ戻して解決

![4回目のレンダリング。箱状の本体にかまぼこ型の蓋と金具が付き、宝箱として認識できる](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/chest-iteration-4.webp)

4回目で宝箱として通る形にはなった。ただし直した内容は3Dの造形知識ではなく、ほぼBlender APIのクセである。

### 課題2: 要件つきのレトロ自動販売機

次に、寸法・部品・ポリゴン上限・PBRを指定した課題を与えた。仕様は0.9×0.8×1.9m、`display_window` / `payment_panel` / `product_buttons` / `rear_panel`を独立オブジェクトとして持つこと、30,000面以下、Principled BSDFを使うこと、床に接地していること。これを12項目の機械検査へ落として、生成のたびに走らせた。検査はMCP経由で流し込む`bpy`スクリプトで、要点だけ書くと次のような内容になる。

```python
# 仕様との突き合わせ（抜粋）
for i, axis in enumerate("XYZ"):
    want, got = SPEC["dimensions_m"][i], bbox[i]
    checks.append({"check": f"dimension_{axis}", "want": want, "got": got,
                   "pass": abs(got - want) <= want * 0.02})

for part in SPEC["required_parts"]:            # 部品が独立オブジェクトとして在るか
    ok = any(part in o.name.lower() for o in meshes)
    checks.append({"check": f"part:{part}", "got": ok, "pass": ok})

checks.append({"check": "on_ground", "got": min_z, "pass": abs(min_z) < 0.005})
checks.append({"check": "max_faces", "got": total_faces,
               "pass": total_faces <= SPEC["max_faces"]})
```

1回目は12項目中11項目通過。落ちたのは奥行きで、前面パーツと背面パネルを本体表面より外側へ置いたため0.88mになっていた。前後4cmのはみ出しは、レンダリングを見ても気づけない。

2回目、パーツを本体表面と面一に直すと検査は12/12になった。ところが見た目は悪化する。

![面一に直したあとのレンダリング。窓とパネルの面が本体と重なり、縞状のZ-fightingが出ている](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/vending-flush-zfighting.webp)

同一平面に2つの面が重なってZ-fightingが発生した。機械検査は満点、見た目は破綻という状態である。

3回目、許容差（±2%）の内側で2mmだけ前へ出して、検査12/12・表示も正常になった。最終のバウンディングボックスは0.9×0.804×1.9m、総ポリゴン数は66面。

![完成した自動販売機のレンダリング。赤い筐体に商品窓、決済パネル、選択ボタン、取り出し口が付いている](/assets/images/posts/2026-07-30-blender-mcp-3d-generation-workflow/vending-final.webp)

書き出しでも1回失敗している。`bpy.ops.export_mesh.stl`を呼んで「演算子が見つからない」で落ちた。Blender 4.xでSTLエクスポータが`bpy.ops.wm.stl_export`へ移っているためである。呼び直して、`.blend`（562KB）、GLB（17.4KB）、STL（6.5KB）、FBX（56.4KB）はいずれも出力できた。

### 検証Dで分かったこと

Blender側の処理時間はレンダリング以外すべて1秒未満で、レンダリングも3〜4秒だった。つまりMCP越しの往復は律速ではない。時間を使ったのは失敗の診断と書き直しで、これはエージェント側の仕事である。

収穫は、機械検査と見た目評価が**別々の失敗を拾った**ことだった。1回目の自動販売機は見た目は自然だが寸法が外れており、2回目は検査満点で見た目が破綻していた。片方だけでは、どちらの回も合格として通ってしまう。前節で分けたValidator（数値）とVisual Critic（画像）を別の役割にしておく設計は、この規模の課題でも意味があった。

一方で、失敗の中身は「3Dの知識」というより「Blender APIのクセ」に寄っていた。`transform_apply`の既定引数、4.xでの演算子の改名、`bisect_plane`が期待通りに効かないこと。これはドキュメントを読める人なら潰せるが、3D未経験者が症状（部品が浮く）から原因（位置がメッシュに焼き込まれた）へ到達するのは難しい。裏を返すと、この層こそSkillとして固定する価値がある部分で、実際に今回書いた検査スクリプトは、そのまま`validate_mesh`の原型になっている。

最後に、この結果を過大評価しないための注意も書いておく。作ったのは66面の箱組みで、プリミティブを並べれば成立する課題である。曲面や有機的な形状、テクスチャの質は今回まったく試していない。同一条件で3回実行するばらつきの測定もしていない。同じセッションのLLMは前の失敗を覚えているため独立試行にならず、意味のある数字を出すにはセッションを分けて回す必要がある。

## 残る検証（BとE）

BとEは初期メッシュの生成源が必要なため未実施である。実施するなら次の順で進める。

1. **B: Image-to-3Dのみ** — 課題2と同じ仕様書から参照画像を作り、Meshy / TripoのAPI（またはHunyuan3Dの自己ホスト）で初期メッシュを生成する。検証Dで使った12項目の検査をそのまま走らせれば、Dと同じ土俵で比較できる
2. **E: Image-to-3D → Blender MCP** — Bの出力をインポートし、寸法の正規化・部品分割・検査・修正をBlender MCP側で反復する
3. DとBの差が確認できた段階で、Planner-Actor-Critic的な役割分担やSkill化を足し、改善量を測る

BとEでは、Dでは測れなかった項目が主な観測対象になる。

- 指示との外観一致、背面を含む形状の破綻
- トポロジーと編集しやすさ
- テクスチャ・PBRの品質
- 手で直した回数、完成までの所要時間、クレジット費用
- 同一条件で3回実行したときのばらつき（セッションを分けて実行する）
- 最終用途にそのまま使えるか

とくにライセンスは実行前に確認する必要があり、Tripoの無料プランは商用利用不可、Hunyuan3D 2.1は地域制限がある。

### 実験ログのテンプレート

BとEを実施する際は、次のテンプレートを実行ごとに複製して記録する。検証Dの記録もこの形式で取った。

```markdown
## Run ID

- Date:
- Tool / Model:
- Input prompt:
- Reference images:
- Parameters / seed:
- Generated files:
- Time:
- Cost:

### Automatic checks
- Dimensions:
- Faces / vertices:
- Non-manifold:
- UV / materials:

### Human evaluation
- Appearance match (1-5):
- Requirement match (1-5):
- Editability (1-5):
- Usable without manual repair: Yes / No

### Failures

### Manual operations required

### Next instruction
```

## 安全性・費用・ライセンスの注意点

記事全体を通じて確認した注意点を改めてまとめる。

- Blender MCPの任意コード実行は、ローカル限定運用・実行前確認・Safe Mode的な制限のいずれかを組み合わせて使う。検証Dで実際にモデルを作った操作はすべて`execute_blender_code`経由であり、この機能を切ると使えるのは情報取得だけになる
- テレメトリは既定で有効になっている。送信を止めるなら`DISABLE_TELEMETRY=true`を環境変数で渡し、Add-onの設定でも同意状態を確認する
- Hunyuan3D系のモデルは独自ライセンスで、EU・英国・韓国での利用や大規模商用利用に制約がある
- Meshy・Tripoの無料プランは商用利用可否やクレジット数がプランで異なるため、用途に応じて確認する
- 3Dプリントや製造用途では、AIによる見た目の評価だけで安全性・強度・寸法精度を保証しない
- 料金・モデル名・ライセンス条件は変わりやすいため、この記事の数値は2026年7月時点のものとして扱ってほしい

## 結論：知識は不要になるのではなく、必要な知識の位置が変わる

現時点では、生成AIによって3Dの専門知識が完全に不要になったとは言いにくい。トポロジー、寸法、用途別の制約、失敗時の診断には、依然として知識が求められる。

一方で、初心者がゼロからすべてを手作業で行う必要は大きく減っている。初期案と初期メッシュの生成、Blender操作の代行、定型的な修正、レンダリングと比較、数値的な品質検査、失敗理由の説明をAIに担当させることで、必要な知識を「制作操作」から「目的と評価基準の指定」へ移せる可能性がある。

検証Dの範囲で言えば、要件を12項目の検査へ落としてから反復すると、3回目で仕様を満たすところまでは来た。ただしその過程で直したのは造形ではなくBlender APIの扱いで、症状から原因へ辿る部分は今もエージェント側の仕事だった。「プロンプト一発で作れた」というデモよりも、失敗を診断して反復できる仕組みを組めるかどうかが実用の分かれ目になる、という当初の見立ては変えていない。Image-to-3Dを組み合わせた場合にこの構図がどう変わるかは、BとEの検証で確かめる。

## 参考

- [ahujasid/blender-mcp — GitHub](https://github.com/ahujasid/blender-mcp)
- [Claude for Creative Work \\ Anthropic](https://www.anthropic.com/news/claude-for-creative-work)
- [Anthropic joins the Blender Development Fund as Corporate Patron — Blender](https://www.blender.org/archive/anthropic-joins-the-blender-development-fund-as-corporate-patron/)
- [Anthropic's patronage of Blender downgraded to one-off donation | CG Channel](https://www.cgchannel.com/2026/05/anthropics-patronage-of-blender-downgraded-to-one-off-donation/)
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)
- [djeada/blender-mcp-server](https://github.com/djeada/blender-mcp-server)
- [Meshy Pricing](https://www.meshy.ai/pricing)
- [Tencent-Hunyuan/Hunyuan3D-2.1 LICENSE](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE)
- [EZBlender: Efficient 3D Editing with Plan-and-ReAct Agent (arXiv:2601.07143)](https://arxiv.org/abs/2601.07143)
- [From Idea to Co-Creation: A Planner-Actor-Critic Framework for Agent Augmented 3D Modeling (arXiv:2601.05016)](https://arxiv.org/abs/2601.05016)
- [Hunyuan3D 2.0 (arXiv:2501.12202)](https://arxiv.org/abs/2501.12202)
