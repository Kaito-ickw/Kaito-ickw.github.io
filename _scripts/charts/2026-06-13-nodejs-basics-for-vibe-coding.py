"""Node.js入門記事の図。"""
from diagram import Section, figure, write_figure

SLUG = "2026-06-13-nodejs-basics-for-vibe-coding"

write_figure(SLUG, "npm-run-dev-flow.svg", figure(
    "npmdev",
    "npm run dev が開発サーバーを起動するまで",
    "AIエージェントがnpm run devを実行すると、package.jsonが読まれ、"
    "そこに書かれたViteやNext.jsといったツールがNode.js上で動き、開発サーバーが立ち上がる。",
    [Section(
        nodes=[("agent", "AIエージェント"), ("cmd", "npm run dev", "accent"),
               ("pkg", "package.json"), ("tool", "Vite / Next.js など"),
               ("run", "Node.js上で実行"), ("dev", "開発サーバー", "accent")],
        edges=[("agent", "cmd"), ("cmd", "pkg"), ("pkg", "tool"),
               ("tool", "run"), ("run", "dev")],
    )]))

write_figure(SLUG, "nodejs-role.svg", figure(
    "role",
    "Node.jsが担っているもの",
    "React・TypeScriptのソースはNode.js上の開発ツールが処理し、"
    "開発サーバーとしてブラウザで確認する経路と、ブラウザ向け成果物としてデプロイする経路に分かれる。",
    [Section(
        nodes=[("src", "React / TypeScript のソース"),
               ("tools", "Node.js上の開発ツール", "accent"),
               ("dev", "開発サーバー"), ("build", "ブラウザ向け成果物"),
               ("browser", "ブラウザで確認"), ("deploy", "デプロイ")],
        edges=[("src", "tools"), ("tools", "dev"), ("tools", "build"),
               ("dev", "browser"), ("build", "deploy")],
    )]))

write_figure(SLUG, "npm-script-resolution.svg", figure(
    "resolve",
    "npm run dev が解決される順",
    "npm run devはpackage.jsonを読み、scripts.devの定義を探し、"
    "そこに書かれたviteを実行して開発サーバーを起動する。",
    [Section(
        nodes=[("cmd", "npm run dev", "accent"), ("pkg", "package.json を読む"),
               ("script", "scripts.dev を探す"), ("vite", "vite を実行する"),
               ("dev", "開発サーバーが起動する")],
        edges=[("cmd", "pkg"), ("pkg", "script"), ("script", "vite"), ("vite", "dev")],
    )]))

write_figure(SLUG, "dependency-install.svg", figure(
    "install",
    "package.json と package-lock.json の役割の違い",
    "package.jsonが許容するバージョンの範囲を、package-lock.jsonが具体的な依存関係を持ち、"
    "npm installが両方を読んでnode_modulesを作る。",
    [Section(
        nodes=[("pkg", "package.json\n許容するバージョン"),
               ("lock", "package-lock.json\n具体的な依存関係"),
               ("install", "npm install", "accent"), ("mods", "node_modules")],
        edges=[("pkg", "install"), ("lock", "install"), ("install", "mods")],
        layers=[["pkg", "lock"], ["install"], ["mods"]],
    )]))

write_figure(SLUG, "npm-script-hooks.svg", figure(
    "hooks",
    "prebuild と postbuild が呼ばれる順",
    "npm run buildを実行すると、prebuildが事前処理として、buildが本処理として、"
    "postbuildが事後処理として、この順に自動で呼ばれる。",
    [Section(
        nodes=[("pre", "prebuild\n事前処理"), ("main", "build\n本処理", "accent"),
               ("post", "postbuild\n事後処理")],
        edges=[("pre", "main"), ("main", "post")],
    )]))
