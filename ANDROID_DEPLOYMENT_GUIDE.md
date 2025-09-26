# Android Deployment Guide for お小遣い帳 (Allowance App)

このガイドでは、Python-for-Android (Py4A) と Buildozer を使用して、Pythonベースのお小遣い帳アプリをAndroidスマートフォンにデプロイする手順を説明します。

## 1. 前提条件

始める前に、開発マシンに以下のものがインストールされ、設定されていることを確認してください。

### 1.1 Java Development Kit (JDK)
Android開発にはJDKが必要です。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** Webブラウザ、ターミナル/コマンドプロンプト

1.  最新のLTSバージョンのOracle JDKまたはOpenJDK（例: JDK 11またはJDK 17）をWebブラウザでダウンロードし、開発マシンにインストールします。
2.  ターミナルまたはコマンドプロンプトで、`JAVA_HOME` 環境変数をJDKのインストールディレクトリに設定します。

### 1.2 Android Studio
Android Studioは、Android SDK、プラットフォームツール、およびエミュレータ（テストにはオプションですが推奨）を提供します。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** Webブラウザ、Android Studioアプリケーション、ターミナル/コマンドプロンプト

1.  [Android Studio](https://developer.android.com/studio) をWebブラウザでダウンロードし、開発マシンにインストールします。
2.  インストール中に、Android SDKと少なくとも1つのAndroidプラットフォーム（例: Android 10.0以降）をインストールしていることを確認します。
3.  `ANDROID_HOME` 環境変数をAndroid SDKのインストールディレクトリ（通常、Linux/macOSでは `~/Android/sdk`、Windowsでは `%LOCALAPPDATA%\Android\sdk`）に設定します。
4.  Android SDKプラットフォームツールをシステムのPATHに追加します。例えば、Linux/macOSではターミナルで以下を実行します。
    ```bash
    export PATH=$PATH:$ANDROID_HOME/platform-tools
    ```

### 1.3 Androidスマートフォンで開発者向けオプションとUSBデバッグを有効にする
コンピュータから直接スマートフォンにアプリをインストールするには、以下の設定が必要です。

**どこで作業するか:** Androidスマートフォン
**何を使って作業するか:** スマートフォンの設定アプリ

1.  スマートフォンの **設定** アプリを開きます。
2.  下にスクロールして **端末情報** （または **デバイス情報**）をタップします。
3.  **ビルド番号** を見つけて、7回連続で素早くタップします。「これでデベロッパーになりました！」というメッセージが表示されるはずです。
4.  **設定** に戻ると、新しいオプション **開発者向けオプション** が表示されます。
5.  **開発者向けオプション** をタップします。
6.  **USBデバッグ** を有効にします。
7.  USBケーブルでスマートフォンをコンピュータに接続します。スマートフォンにプロンプトが表示されたら、コンピュータからのUSBデバッグを許可します。

## 2. Buildozerを使用したPython-for-Android (Py4A) のセットアップ

Buildozerは、PythonアプリケーションをAndroid向けにパッケージ化するプロセスを簡素化します。

### 2.1 Buildozerのインストール

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

ターミナルまたはコマンドプロンプトを開き、Buildozerをインストールします。
```bash
pip install buildozer
```

### 2.2 プロジェクトのBuildozerの初期化

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

プロジェクトのルートディレクトリ（`allowance.py` がある場所）に移動します。
```bash
cd /Users/minamidenshiimanaka/AI/okodukai
```
Buildozerの初期化を実行します。
```bash
buildozer init
```
このコマンドは、プロジェクトディレクトリに `buildozer.spec` ファイルを作成します。このファイルには、Androidアプリケーションのすべての設定が含まれています。

## 3. Android用Pythonアプリケーションの準備

現在の `allowance.py` はHTTPサーバーを実行します。Androidの場合、このサーバーを起動するメインのエントリポイントが必要です。

### 3.1 `main.py` の作成

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** テキストエディタ

プロジェクトのルートディレクトリに `main.py` という名前の新しいファイルを作成し、以下の内容を記述します。

```python
import os
import sys
from allowance import main as allowance_main # Import the main function from allowance.py

# This is a placeholder for the webview integration.
# For now, we'll just start the Python server.
# In a more complex setup, you might integrate with a WebView directly here.

if __name__ == '__main__':
    # Ensure the current directory is in sys.path for imports to work
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Start the allowance app's HTTP server
    allowance_main()
```

### 3.2 `buildozer.spec` の変更

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** テキストエディタ

ステップ2.2で作成された `buildozer.spec` ファイルを開きます。以下の行を変更する必要があります。

-   **`title`**: アプリケーションのタイトル（例: `お小遣い帳`）。
-   **`package.name`**: ユニークなパッケージ名（例: `org.yourcompany.allowanceapp`）。
-   **`package.domain`**: あなたのドメイン（例: `yourcompany.com`）。
-   **`source.dir`**: Pythonソースコードを含むディレクトリ。このプロジェクトでは `.` （現在のディレクトリ）である必要があります。
-   **`requirements`**: `python3`, `kivy` （BuildozerはUIにKivyを使用することが多いですが、サーバーを実行するだけであってもPython環境を提供します）、`requests` （アプリが使用する場合、`allowance.py` は `http.server` を使用しますが）および `allowance.py` が依存するその他のPythonライブラリを追加します。`allowance.py` の場合、標準ライブラリモジュールを使用しているため `python3` で十分です。
    ```ini
    requirements = python3,kivy
    ```
    *(注: Kivyは通常、Androidアプリを作成するためのBuildozerの基盤となるメカニズムによってデフォルトで含まれるか、必要とされます。UIにKivyを使用していなくても、Python環境のセットアップに役立ちます。)*
-   **`android.api`**: ターゲットAndroid APIレベル（例: `27` またはそれ以上）。
-   **`android.minapi`**: サポートされる最小Android APIレベル（例: `21`）。
-   **`android.permissions`**: 必要なパーミッションを追加します。Webサーバーの場合、インターネットアクセスが必要です。
    ```ini
    android.permissions = INTERNET
    ```
-   **`fullscreen`**: 標準のアプリウィンドウが必要な場合は `0`、フルスクリーンの場合は `1` に設定します。
-   **`orientation`**: `landscape` または `portrait`。

**重要な点として、Webサーバーアプリの場合、`allowance.py` と `main.py` （およびアプリの初期状態の一部であるCSVファイル）を含めるようにBuildozerに指示する必要があります。**
-   **`source.include_exts`**: `.py` が含まれていることを確認します。
-   **`source.exclude_dirs`**: `.git`, `.buildozer` などを除外します。
-   **`source.include_patterns`**: ここにCSVファイルを追加します。
    ```ini
    source.include_patterns = *.py,*.png,*.jpg,*.kv,*.atlas,*.csv
    ```
    `allowance.csv`, `goals.csv`, `presets.csv` が含まれていることを確認してください。

## 4. Androidアプリケーション (APK) のビルド

`buildozer.spec` が設定されたら、Androidアプリケーションをビルドできます。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

### 4.1 以前のビルドのクリーンアップ (オプションですが推奨)
```bash
buildozer clean
```

### 4.2 デバッグAPKのビルド
```bash
buildozer android debug
```
このコマンドは、必要なAndroid SDKコンポーネント、NDK、Python-for-Androidツールチェーンをダウンロードし、PythonコードをコンパイルしてAPKファイルにパッケージ化します。このプロセスは、ビルド環境全体をセットアップするため、初回実行時にはかなりの時間（数十分から数時間）かかる場合があります。

生成されたAPKファイルは、プロジェクト内の `bin/` ディレクトリに配置されます（例: `bin/allowanceapp-0.1-debug.apk`）。

## 5. Androidデバイスへのインストールと実行

### 5.1 APKのインストール

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

AndroidスマートフォンがUSB経由でコンピュータに接続され、USBデバッグが有効になっていることを確認します。
```bash
adb install bin/allowanceapp-0.1-debug.apk
```
`allowanceapp-0.1-debug.apk` を、生成されたAPKファイルの実際の名前で置き換えてください。

### 5.2 アプリケーションの実行

**どこで作業するか:** Androidスマートフォン
**何を使って作業するか:** スマートフォンのホーム画面またはアプリドロワー

インストールが完了すると、スマートフォンのホーム画面またはアプリドロワーに「お小遣い帳」アプリのアイコンが表示されるはずです。アイコンをタップしてアプリケーションを起動します。

アプリは内部でPython HTTPサーバーを起動します。Pythonスクリプトによって提供されるWebインターフェースを表示するには、Androidアプリ内にWebViewを実装する必要がある場合があります。このガイドは、PythonサーバーをAndroidで実行することに焦点を当てています。WebViewとの統合は、Android開発の次のステップになります。

**WebView統合に関する注意:**
上記の `main.py` は単にPythonサーバーを起動するだけです。完全なAndroidアプリでは、通常、Java/KotlinアクティビティがWebViewを作成し、`http://127.0.0.1:8000` （またはPythonサーバーが実行されているポート）を指すようにします。これには、より高度なAndroid開発の知識が必要です。Java/Kotlinを記述せずに、より統合されたエクスペリエンスが必要な場合は、KivyのWebView機能やその他のPythonベースのAndroid用UIフレームワークを検討することもできます。

この最初のデプロイの目標は、PythonサーバーをAndroidで実行することです。その後、Androidデバイスのブラウザで `http://127.0.0.1:8000` にアクセスすることで（アプリがバックグラウンド実行を許可し、ポートがアクセス可能な場合）、アクセスできます。ただし、専用のWebViewがローカルWebアプリを統合する標準的な方法です。