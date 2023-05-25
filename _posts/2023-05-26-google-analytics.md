---
layout: post
title: "JekyllとGitHub PagesでGoogle Analyticsを導入する"
subtitle: "ウェブサイトにリアルタイム分析を取り入れる方法"
categories: Web Development
tags: [Jekyll, GitHub Pages, Google Analytics]
---

GitHub PagesでホストされているJekyllサイトにGoogle Analyticsを導入する方法を解説します。

## はじめに

Google Analyticsは、ウェブサイトのトラフィックを計測するための強力なツールです。この記事では、GitHub PagesでホストされるJekyllサイトにGoogle Analyticsを導入する方法について詳しく説明します。

## Google Analyticsの設定

まず、Google AnalyticsのトラッキングIDが必要です。以下の手順で取得します。

1. Google Analyticsのウェブサイトにアクセスします。
2. 新しいプロパティを作成します。
3. そのプロパティのトラッキングIDを取得します。

取得したトラッキングIDは `G-XXXX` の形式になります。

<!--Google Analyticsのプロパティ設定画面のスクリーンショット挿入予定-->

## Jekyllの設定

次に、Jekyllの設定を行います。まず、サイトの設定ファイル `_config.yml` に取得したトラッキングIDを追加します。

```yaml
# Google analytics
google_analytics: G-XXXX
```

<!--_config.ymlの編集画面のスクリーンショット挿入予定-->

## トラッキングコードの埋め込み

yatテンプレートを使用している場合、Google Analyticsの設定は `extensions/google-analytics.html` という名前のファイルを通じて行われます。

以下のようにGoogle Analytics 4 のトラッキングコードを記述します。
`'G-XXXX'` の部分はGoogle AnalyticsのトラッキングIDに置き換えてください。

```html
<script>
  function initGoogleAnalytics() {
    var doNotTrack = (window.doNotTrack === "1" || navigator.doNotTrack === "1" ||
      navigator.doNotTrack === "yes" || navigator.msDoNotTrack === "1");
    var enableDNT = "{{ site.enableDNT | default: true }}" == "true";

    if (!enableDNT || !doNotTrack) {
      var ga_id = '{{ site.google_analytics }}';

      var script = document.createElement('script');
      script.async = true;
      script.src = 'https://www.googletagmanager.com/gtag/js?id=' + ga_id;
      document.head.appendChild(script);

      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());

      gtag('config', ga_id);
    }
  }
  window.addEventListener("load", initGoogleAnalytics);
</script>
```

<!--google-analytics.htmlの編集画面のスクリーンショット挿入予定-->

## デプロイと確認

以上の設定が完了したら、サイトを再ビルドし、デプロイします。

その後、サイトをブラウザで開き、「ページのソースを表示」をクリックしてHTMLソースコードを確認します。Google Analyticsのトラッキングコードが正しく挿入されていることを確認します。

```html
<script>
  function initGoogleAnalytics() {
    ...
    gtag('config', 'G-XXXX');
  }
  window.addEventListener("load", initGoogleAnalytics);
</script>
```

<!--ブラウザで開いたHTMLソースコードのスクリーンショット挿入予定-->

Google Analyticsでは、データの収集と表示に少し時間がかかることがあります。
デプロイ直後にすぐにデータが表示されない場合でも、しばらく待ってから再度確認してみてください。
10分程度待つと反映されていました。

また、Google Analyticsの「リアルタイム」セクションを利用すると、現在アクティブなユーザー数をリアルタイムで確認できます。これにより、トラッキングコードが正しく機能しているかをすぐに確認できます。

<!--Google Analyticsの「リアルタイム」セクションのスクリーンショット挿入予定-->

## まとめ

以上がJekyllとGitHub PagesでGoogle Analyticsを導入する手順です。適切な設定を行うことで、ウェブサイトのトラフィックを詳細に追跡し、より質の高いコンテンツを作成するための洞察を得ることができます。