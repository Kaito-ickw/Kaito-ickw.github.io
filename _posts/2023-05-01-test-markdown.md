---
layout: post
title: markdown記法チートシート
subtitle: jekyllで使用するmarkdown記法の一覧
categories: markdown
tags: [markdown, cheat sheet]
---

通常の[markdown](http://markdowntutorial.com/)を記述すると、Jekyllにより自動的にWebページに変換されます。markdown記法については、[take 5 minutes to learn how to write in markdown](http://markdowntutorial.com/) がおすすめです。通常のテキストを太字/斜体/見出し/表などに変換する方法を学ぶことができます。

'**'(アスタリスク2つ)で囲うと太字:

**太字のテキスト**

'_'(アンダースコア)で囲うと斜体:

_斜体のテキスト_

## 見出し1
### 見出し2
#### 見出し3
##### 見出し4
###### 見出し5

テーブル:

| Number | Next number | Previous number |
| :------ |:--- | :--- |
| Five | Six | Four |
| Ten | Eleven | Nine |
| Seven | Eight | Six |
| Two | Three | One |


おいしいクレープはいかがですか?

![Crepe](https://s3-media3.fl.yelpcdn.com/bphoto/cQ1Yoa75m2yUFFbY2xwuqw/348s.jpg)

センタリングすることもできます!

![Crepe](https://s3-media3.fl.yelpcdn.com/bphoto/cQ1Yoa75m2yUFFbY2xwuqw/348s.jpg){: .center-block :}

コードブロック:

~~~
var foo = function(x) {
  return(x + 5);
}
foo(3)
~~~

シンタックスハイライト付きの場合:

```javascript
var foo = function(x) {
  return(x + 5);
}
foo(3)
```

行番号付きの場合:

{% highlight javascript linenos %}
var foo = function(x) {
  return(x + 5);
}
foo(3)
{% endhighlight %}

## ボックス
以下のように、通知、警告、エラーボックスを追加することができます。:

### 通知

{: .box-note}
**Note:** 通知ボックスです

### 警告

{: .box-warning}
**Warning:** 警告ボックスです

### エラー

{: .box-error}
**Error:** エラーボックスです
