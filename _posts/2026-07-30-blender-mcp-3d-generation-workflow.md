---
layout: post
title: "生成AIとBlender MCPで、3D未経験者はどこまでモデルを作れるか"
subtitle: Text-to-3DとBlender操作エージェントの役割を分けて考える
categories: AI開発
tags: ["Blender", "MCP", "AIエージェント", "3Dモデリング", "生成AI", "AIセーフティ"]
lang: ja
---

3DモデリングをやったことがなくてもBlender MCPを使えば実用的なモデルが作れる、という話をよく見かけるようになった。テキストや画像から一発でモデルを生成するサービスと、LLMがBlenderを操作するエージェントは、どちらも「AIで3Dを作る」とまとめて語られがちだが、できることの中身はかなり違う。

この記事では両者を区別したうえで、現在の生成AIが得意なこと・苦手なことを整理し、単体利用で起きやすい失敗と、それを減らすための反復ワークフローの設計案までをまとめる。実際の検証は依頼者側で追って実施する前提のため、検証計画までを扱い、実測値が必要な箇所は明示的なTODOとして残す。

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

`ahujasid/blender-mcp`のREADMEには多くの機能が書かれているが、記事化にあたっては「実際に検証した機能」と「README記載のみで未検証の機能」を分けて扱う。

- **確認できた範囲**: シーン情報の取得、オブジェクトの作成・削除・変形、マテリアル・ライト・カメラの制御、任意Pythonコードの実行（`execute_blender_code`）、レンダリング結果の取得、GLB/FBX/STL等へのエクスポート
- **README記載だが本記事執筆時点で未検証**: Poly Havenからのアセット取得、Sketchfabモデルの検索・取り込み、Hyper3D Rodinによる生成モデルの取り込み、Hunyuan3Dとの連携、リモートホストでの利用

この切り分けは、検証セクションで実際に手を動かした後に更新する。

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

## 検証計画（TODO）

以下は検証の設計であり、本記事執筆時点では実測値を含まない。検証結果は依頼者側で実施後、この記事へ追記する。

### 検証の順序

比較する方式は多いが、一度にすべてを試すのではなく、差分が確認しやすい順に進める。

1. **D: Blender MCPのみ**（自然言語操作だけでどこまで作れるか）
2. **B: Image-to-3Dのみ**（生成AI単体の初期メッシュの質）
3. **E: Image-to-3D → Blender MCPによる反復修正**（DとBの組み合わせ）

DとBの結果に明確な差が確認できた段階で、Planner-Actor-Critic的な役割分担やSkill化・RAG的な事例再利用を追加し、その改善効果を測定する。

### テスト課題

<!-- TODO: 実施日・担当・使用ツールバージョンを記入 -->

1. **単純なスタイライズ小物**（例: ローポリの宝箱、植木鉢、ランプ）
2. **要件のあるゲーム用プロップ**（例: レトロ自動販売機。寸法・部品・ポリゴン上限・PBRを指定）
3. **複数オブジェクトの小規模シーン**（例: 机、椅子、照明、小物を含む作業部屋）

### 評価項目

各5段階または実測値で記録する。

- 指示との外観一致
- 寸法・構成要件の達成率
- 背面を含む形状の破綻
- トポロジー・編集しやすさ
- テクスチャ・PBR品質
- Blender初心者が手で直した回数
- 完成までの所要時間、API/クレジット費用
- LLMの試行回数・トークン量
- 再実行時のばらつき（同一条件で最低3回実行して比較する）
- 最終用途にそのまま使えるか

### 実験ログのテンプレート

<!-- TODO: 以下のテンプレートを検証実施ごとに複製して記入する -->

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

- Blender MCPの任意コード実行は、ローカル限定運用・実行前確認・Safe Mode的な制限のいずれかを組み合わせて使う
- Hunyuan3D系のモデルは独自ライセンスで、EU・英国・韓国での利用や大規模商用利用に制約がある
- Meshy・Tripoの無料プランは商用利用可否やクレジット数がプランで異なるため、用途に応じて確認する
- 3Dプリントや製造用途では、AIによる見た目の評価だけで安全性・強度・寸法精度を保証しない
- 料金・モデル名・ライセンス条件は変わりやすいため、この記事の数値は2026年7月時点のものとして扱ってほしい

## 結論：知識は不要になるのではなく、必要な知識の位置が変わる

現時点では、生成AIによって3Dの専門知識が完全に不要になったとは言いにくい。トポロジー、寸法、用途別の制約、失敗時の診断には、依然として知識が求められる。

一方で、初心者がゼロからすべてを手作業で行う必要は大きく減っている。初期案と初期メッシュの生成、Blender操作の代行、定型的な修正、レンダリングと比較、数値的な品質検査、失敗理由の説明をAIに担当させることで、必要な知識を「制作操作」から「目的と評価基準の指定」へ移せる可能性がある。

「プロンプト一発で作れた」という一発生成のデモではなく、3D未経験者でも失敗を診断し、反復して完成へ近づけられる仕組みを作れるかどうかが、この記事で検証したい問いになる。

## 参考

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
