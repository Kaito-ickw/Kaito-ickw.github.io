---
layout: post
title: 【Docker & VSCode】Pythonデータ分析環境の構築と運用
subtitle: VSCodeのRemote Containersを利用して効率的にデータ分析環境を構築する
categories: programming
tags: [Docker, VSCode, Python, Data Analysis]
---

## はじめに

この記事では、VSCodeのRemote Containers拡張機能を利用し、DockerでPythonのデータ分析環境を構築、運用する手法について解説します。

## 前提条件

- Dockerがインストール済みである
- 使用するエディタはVSCode
- ターミナルはVSCode上から利用

## 手順

### 1. プロジェクトディレクトリの作成

環境はプロジェクトごとに用意する想定です。
今回は、 `python_data_analysis_vscode` というプロジェクトを作成していきます。

```bash
mkdir python_data_analysis_vscode
cd python_data_analysis_vscode
```

### 2. Dockerfileの作成

続いて、Dockerfileを作成していきましょう。
Dockerfileには以下の内容を記入します。

```Dockerfile
FROM python:3.9
WORKDIR /workspace
RUN pip install numpy pandas matplotlib seaborn jupyterlab scikit-learn
```

### 3. `.devcontainer/devcontainer.json`の作成

`.devcontainer`ディレクトリ内に`devcontainer.json`を作成します。

```json
{
  "name": "Python Data Analysis",
  "build": {
    "dockerfile": "../Dockerfile",
    "context": ".."
  },
  "extensions": [
    "ms-python.python"
  ],
  "forwardPorts": [8888]
}
```

### 4. Remote Containers拡張機能のインストール

VSCodeで`Remote - Containers`をインストールします。

### 5. Remote Containerの起動

VSCodeでプロジェクトディレクトリを開き、Remote Containerを起動します。

### 6. Jupyter Labの起動

```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

## まとめ

VSCodeとDockerを組み合わせることで、カスタマイズしたPythonデータ分析環境を簡単に構築、運用することができます。
特にRemote Containers拡張は、環境設定の手間を大きく削減してくれます。
