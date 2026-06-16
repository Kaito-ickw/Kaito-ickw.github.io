---
layout: post
title: "OpenAIはなぜ「スクリーンのない」AIデバイスを作ろうとしているのか"
subtitle: Jony Iveとの提携が目指す体験と、2027年延期までの経緯
categories: AI開発
tags: ["OpenAI", "AI", "AIネイティブ開発", "ハードウェア"]
lang: ja
---

ChatGPTはブラウザやスマートフォンのアプリとして使うのが当たり前になっている。だがOpenAIは、その先に専用のハードウェアを置こうとしている。元Appleのデザイン責任者Jony Iveを巻き込んだこの計画は、2025年の発表以来何度も報道されてきたが、ブランド名の変更や発売延期もあり、全体像が見えにくくなっている。

ここでは公開されている報道をもとに、OpenAIが何を作ろうとしていて、どういう体験を目指しているのかを整理する。

## 結論を先に

OpenAIが目指しているのは、スマートフォンを置き換える単一の新製品ではなく、スマートフォンやノートPCと並ぶ「もう一つのコアデバイス」だ。画面を持たず、音声と常時的なコンテキスト理解を軸にした、より落ち着いた使用感を狙っている。

具体的な製品名・形状・発売日はまだ確定していない。2025年5月にJony Iveの会社io Productsを買収して始まったこの計画は、当初2026年後半の発表を目指していたが、商標紛争などを経て2027年へ延期されている。

## Jony Iveの会社買収から始まった計画

OpenAIは2025年5月、元Appleのデザイン責任者Jony Iveが率いるスタートアップ「io Products」を、全株式交換で約65億ドルと評価される取引で買収すると発表した。買収は同年7月に完了し、Iveと彼のデザイン集団LoveFromがOpenAIのクリエイティブ・デザイン部門を率いる体制になった（[TechCrunch](https://techcrunch.com/2025/05/21/jony-ive-to-lead-openais-design-work-following-6-5b-acquisition-of-his-company), [MacRumors](https://www.macrumors.com/2025/07/09/openai-jony-ive-io-acquisition-complete/)）。

OpenAIが公開した連名のレターでは、Sam AltmanとJony Iveが「新しい製品群を開発・設計・製造するという野心は、まったく新しい会社を必要とすることが明らかになった」と説明している（[Dezeen](https://www.dezeen.com/2025/05/21/jony-ive-openai-products-merge/)経由で確認）。ソフトウェア企業だったOpenAIが、なぜハードウェアの自社開発に踏み出すのかという問いに対する、当事者なりの回答といえる。

## 目指している体験は「スマホ的な忙しさ」からの距離

Altmanは複数のインタビューで、この計画の狙いを現在のデバイス体験への違和感として語っている。Nikkei Asiaのインタビューを引用した報道によれば、Altmanは今のデバイスを使う感覚を「ニューヨークのタイムズスクエアを歩いているようなもので、光が顔に当たり、人にぶつかられ、常に音が鳴っている」と表現した。一方で目指す体験は「湖畔の美しい山小屋に座って、静けさを楽しんでいる」感覚だという（[Tom's Guide](https://www.tomsguide.com/ai/thats-it-its-so-simple-openais-sam-altman-teases-screenless-device-with-jony-ive)、[WebProNews](https://www.webpronews.com/sam-altman-jony-ive-team-on-ai-device-to-surpass-smartphones-by-2027/)）。

この発言は、デバイスの仕様よりも設計思想を示すものとして報じられている。通知や画面に追われる状態から離れ、声で話しかければ文脈を理解して反応する、背景に存在するAIという方向性だ。報道では「スマートフォンを置き換える」という表現と、「スマートフォンやノートPCと並ぶ第三のコアデバイス」という表現の両方が使われており、最終的にどちらの位置づけになるかはまだ固まっていないようにみえる（[Built In](https://builtin.com/articles/openai-device)、[9to5Mac](https://9to5mac.com/2026/02/10/jony-ives-ai-hardware-is-delayed-to-2027-and-wont-be-called-io/)）。

## 検討されてきた形状は一つではない

報道を時系列で追うと、想定されている形状は一度に決まったわけではなく、複数の方向性が並行して検討されてきたことが分かる。

2025年後半から2026年初頭にかけての報道では、耳の後ろに着けるイヤフォン型のウェアラブルが軸になっていた。コードネーム「Sweetpea」と呼ばれ、環境センサーと専用チップを使い、画面なしで常時情報にアクセスできる構成だと報じられている。同時に、ペン型のデバイス「Gumdrop」も別の形として検討されているとされた（[Geeky Gadgets](https://www.geeky-gadgets.com/io-openai-ai-assistant-2026-launch/)、[Android Headlines](https://www.androidheadlines.com/2026/01/openai-first-device-jony-ive-launch-2026-sweetpea.html)）。TechCrunchも2026年1月、OpenAIが最初の製品としてイヤフォンを検討しており、独自シリコンとOpenAIのモデルを密に統合した音声中心の操作を想定していると報じた。

一方、2026年2月の延期報道以降は、デバイスを「ウェアラブルでもイヤフォン型でもない」とし、デスクに置くか、ポケットに入れて持ち歩く「第三のコアデバイス」として説明する報道に変わっている（9to5Mac）。これが設計方針の転換なのか、報道の解釈の違いなのかは、現時点の公開情報だけでは判断できない。

## ブランド名「io」を捨てた理由

2026年2月、OpenAIはこの計画で使っていた「io」というブランド名の使用を取りやめた。背景にあるのは、補聴器スタートアップ「iyO」が起こした商標権侵害訴訟だ。OpenAIのVPであるPeter Welinderは、「io」「iyO」、いずれの大文字小文字表記も使わないと社内向けに説明したと報じられている（9to5Mac、[Technobezz](https://www.technobezz.com/news/openai-drops-io-branding-for-ai-hardware-and-delays-device-to-2027)）。

新しいブランド名はまだ公表されておらず、報道では一貫して「(io改め)OpenAIのハードウェアデバイス」のような表現が使われている。

## 量産体制は中国依存を避ける方向に

製造面では、2026年1月以降、生産委託先を中国のLuxshareから台湾のFoxconnへ切り替えたという報道が相次いだ。背景として、中国本土での製造に伴うリスクを避けたい意図が指摘されている。組み立て拠点はベトナムまたは米国になる可能性が報じられており、初年度の出荷目標は4,000万〜5,000万台とされている（[Benzinga](https://www.benzinga.com/markets/tech/26/01/49661988/openai-shifts-ai-hardware-manufacturing-to-foxconn-as-jony-ive-designed-device-targets-2026-launch-report)、[TrendForce](https://www.trendforce.com/news/2026/01/02/news-openai-reportedly-shifts-first-ai-hardware-order-from-chinas-luxshare-to-foxconn/)）。

これだけの量産規模を最初から想定している点は、試作機を少量出すプロダクトではなく、最初からマスマーケットを狙っていることを示している。

## 発売は2027年に後ろ倒し

当初、デバイスは2026年後半の発表が目標とされていた。しかし2026年2月の報道では、顧客への出荷は「2027年2月末より前にはならない」とされ、計画が後ろ倒しになったことが明らかになった（[PYMNTS](https://www.pymnts.com/artificial-intelligence-2/2026/openai-delays-first-consumer-device-to-2027/)、[9to5Mac](https://9to5mac.com/2026/02/10/jony-ives-ai-hardware-is-delayed-to-2027-and-wont-be-called-io/)）。

延期の理由として公開報道で確認できるのは、前述の商標紛争への対応と、ハードウェア・ソフトウェア両面の完成度を上げるための調整だ。PYMNTSの報道では、延期によって「モデルの精度を高め、デバイス上の処理を最適化し、デザインを練り直す」ための時間を確保すると説明されている。OpenAIの経営判断の優先順位について踏み込んだ独自の説明は、今回確認した公開ソースの範囲では見当たらなかった。

## まとめ

| 項目 | 内容 |
| :--- | :--- |
| 計画の起点 | 2025年5月、Jony Ive率いるio Productsを約65億ドルで買収（同年7月完了） |
| 目指す体験 | 画面に追われない、声とコンテキスト理解を軸にした「落ち着いた」AI体験 |
| 位置づけ | スマートフォン・ノートPCと並ぶ「第三のコアデバイス」という説明が中心 |
| 検討された形状 | イヤフォン型「Sweetpea」、ペン型「Gumdrop」など複数案 |
| ブランド名 | 商標紛争を理由に「io」の使用を停止。新名称は未公表 |
| 製造体制 | LuxshareからFoxconnへ切り替え、初年度4,000万〜5,000万台規模を想定 |
| 発売時期 | 当初2026年後半目標 → 2027年2月末以降に延期 |
| 現状 | 試作機の存在は報じられているが、正式な仕様・名称・発売日は未確定 |

ここまでの情報はすべて2026年6月時点の報道に基づく。OpenAIは正式な製品発表をまだ行っておらず、形状や発売時期は今後さらに変わる可能性がある。

## 参考

- [A letter from Sam & Jony | OpenAI](https://openai.com/sam-and-jony/)
- [Jony Ive to lead OpenAI's design work following $6.5B acquisition of his company - TechCrunch](https://techcrunch.com/2025/05/21/jony-ive-to-lead-openais-design-work-following-6-5b-acquisition-of-his-company)
- [OpenAI Finalizes Deal for Jony Ive's 'io' AI Hardware Company - MacRumors](https://www.macrumors.com/2025/07/09/openai-jony-ive-io-acquisition-complete/)
- [Jony Ive and OpenAI join forces to create "new family of products" - Dezeen](https://www.dezeen.com/2025/05/21/jony-ive-openai-products-merge/)
- ['That's it? It's so simple': OpenAI's Sam Altman teases screenless device with Jony Ive - Tom's Guide](https://www.tomsguide.com/ai/thats-it-its-so-simple-openais-sam-altman-teases-screenless-device-with-jony-ive)
- [Sam Altman, Jony Ive Team on AI Device to Surpass Smartphones by 2027 - WebProNews](https://www.webpronews.com/sam-altman-jony-ive-team-on-ai-device-to-surpass-smartphones-by-2027/)
- [What Is the OpenAI AI Smartphone? Everything We Know About the Jony Ive Device - Built In](https://builtin.com/articles/openai-device)
- [Official: OpenAI to Reveal Its First AI Hardware in Late 2026 - Android Headlines](https://www.androidheadlines.com/2026/01/openai-first-device-jony-ive-launch-2026-sweetpea.html)
- [OpenAI and Jony Ive IO device, AI hardware expected in 2026 - Geeky Gadgets](https://www.geeky-gadgets.com/io-openai-ai-assistant-2026-launch/)
- [Jony Ive's AI hardware is delayed to 2027 and won't be called io - 9to5Mac](https://9to5mac.com/2026/02/10/jony-ives-ai-hardware-is-delayed-to-2027-and-wont-be-called-io/)
- [OpenAI Drops io Branding for AI Hardware and Delays Device to 2027 - Technobezz](https://www.technobezz.com/news/openai-drops-io-branding-for-ai-hardware-and-delays-device-to-2027)
- [OpenAI Delays First Consumer Device to 2027 - PYMNTS](https://www.pymnts.com/artificial-intelligence-2/2026/openai-delays-first-consumer-device-to-2027/)
- [OpenAI Shifts AI Hardware Manufacturing To Foxconn As Jony Ive-Designed Device Targets 2026 Launch: Report - Benzinga](https://www.benzinga.com/markets/tech/26/01/49661988/openai-shifts-ai-hardware-manufacturing-to-foxconn-as-jony-ive-designed-device-targets-2026-launch-report)
- [OpenAI Reportedly Shifts First AI Hardware Order from China's Luxshare to Foxconn - TrendForce](https://www.trendforce.com/news/2026/01/02/news-openai-reportedly-shifts-first-ai-hardware-order-from-chinas-luxshare-to-foxconn/)
