# Android Deployment Guide for お小遣い帳 (Allowance App)

このガイドでは、Python-for-Android (Py4A) と Buildozer を使用して、Pythonベースのお小遣い帳アプリをAndroidスマートフォンにデプロイする手順を、**どの端末で、何を使って、どう操作するか** を明確にしながら説明します。

## 1. 前提条件

始める前に、**開発マシン** に以下のものがインストールされ、設定されていることを確認してください。

### 1.1 Java Development Kit (JDK)
Android開発にはJDKが必要です。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** Webブラウザ、ターミナル/コマンドプロンプト

1.  **JDKのインストール状況の確認:**
    *   **開発マシン** で **ターミナル** (macOS/Linux) または **コマンドプロンプト/PowerShell** (Windows) を開きます。
    *   以下のコマンドを入力してEnterキーを押します。
        ```bash
        java -version
        javac -version
        ```
    *   もしバージョン情報が表示されれば、JDKはインストールされています。表示されない場合やエラーが出る場合は、次のステップに進みます。

2.  **JDKのダウンロードとインストール:**
    *   **開発マシン** で **Webブラウザ** を開き、最新のLTSバージョンのOracle JDKまたはOpenJDK（例: JDK 11またはJDK 17）をダウンロードします。
    *   ダウンロードしたインストーラーを実行し、画面の指示に従ってインストールを完了します。

3.  **`JAVA_HOME` 環境変数の設定:**
    *   **開発マシン** で **ターミナル** または **コマンドプロンプト/PowerShell** を開きます。
    *   JDKのインストールディレクトリ（例: `/Library/Java/JavaVirtualMachines/jdk-17.0.1.jdk/Contents/Home` on macOS, `C:\Program Files\Java\jdk-17` on Windows）を確認します。
    *   以下のコマンドを入力してEnterキーを押し、`JAVA_HOME` 環境変数を設定します。お使いのOSに合わせて適切なコマンドを使用してください。
        *   **macOS/Linux (Bash/Zsh):**
            ```bash
            export JAVA_HOME="/path/to/your/jdk"
            export PATH=$JAVA_HOME/bin:$PATH
            # .bashrc または .zshrc に追加して永続化することを推奨
            echo 'export JAVA_HOME="/path/to/your/jdk"' >> ~/.zshrc
            echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
            source ~/.zshrc
            ```
        *   **Windows (Command Prompt):**
            ```cmd
            set JAVA_HOME="C:\Program Files\Java\jdk-17"
            set PATH=%JAVA_HOME%\bin;%PATH%
            rem システムの環境変数設定から永続化することを推奨
            ```
        *   **Windows (PowerShell):**
            ```powershell
            $env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
            $env:Path = "$env:JAVA_HOME\bin;$env:Path"
            # システムの環境変数設定から永続化することを推奨
            ```

### 1.2 Android Studio
Android Studioは、Android SDK、プラットフォームツール、およびエミュレータ（テストにはオプションですが推奨）を提供します。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** Webブラウザ、Android Studioアプリケーション、ターミナル/コマンドプロンプト

1.  **Android Studioのインストール状況の確認:**
    *   **開発マシン** でAndroid Studioがインストールされていることを確認します。インストールされていない場合は、[Android Studioの公式ウェブサイト](https://developer.android.com/studio) からダウンロードし、画面の指示に従ってインストールします。

2.  **Android SDKコンポーネントの確認とインストール:**
    *   **開発マシン** で **Android Studioアプリケーション** を起動します。
    *   ウェルカム画面またはプロジェクトを開いた後、「File」>「Settings」（macOSでは「Android Studio」>「Preferences」）に移動します。
    *   左側のメニューから「Appearance & Behavior」>「System Settings」>「Android SDK」を選択します。
    *   「SDK Platforms」タブで、少なくとも1つのAndroid Platform（例: Android 10.0 (API Level 29) またはそれ以降）が「Installed」と表示されていることを確認します。インストールされていない場合は、チェックボックスをオンにして「Apply」をクリックし、インストールします。
    *   「SDK Tools」タブで、「Android SDK Build-Tools」、「Android SDK Platform-Tools」、「Android SDK Command-line Tools」がインストールされていることを確認します。インストールされていない場合は、チェックボックスをオンにして「Apply」をクリックし、インストールします。

3.  **`ANDROID_HOME` 環境変数の設定:**
    *   **開発マシン** で **ターミナル** または **コマンドプロンプト/PowerShell** を開きます。
    *   Android SDKのインストールディレクトリ（通常、Linux/macOSでは `~/Android/sdk`、Windowsでは `%LOCALAPPDATA%\Android\sdk`）を確認します。
    *   以下のコマンドを入力してEnterキーを押し、`ANDROID_HOME` 環境変数を設定します。お使いのOSに合わせて適切なコマンドを使用してください。
        *   **macOS/Linux (Bash/Zsh):**
            ```bash
            export ANDROID_HOME="/path/to/your/android/sdk"
            # .bashrc または .zshrc に追加して永続化することを推奨
            echo 'export ANDROID_HOME="/path/to/your/android/sdk"' >> ~/.zshrc
            source ~/.zshrc
            ```
        *   **Windows (Command Prompt):**
            ```cmd
            set ANDROID_HOME="C:\Users\YourUser\AppData\Local\Android\sdk"
            rem システムの環境変数設定から永続化することを推奨
            ```
        *   **Windows (PowerShell):**
            ```powershell
            $env:ANDROID_HOME = "C:\Users\YourUser\AppData\Local\Android\sdk"
            # システムの環境変数設定から永続化することを推奨
            ```

4.  **Android SDKプラットフォームツールをPATHに追加:**
    *   **開発マシン** で **ターミナル** または **コマンドプロンプト/PowerShell** を開きます。
    *   以下のコマンドを入力してEnterキーを押し、PATHに追加します。お使いのOSに合わせて適切なコマンドを使用してください。
        *   **macOS/Linux (Bash/Zsh):**
            ```bash
            export PATH=$PATH:$ANDROID_HOME/platform-tools
            # .bashrc または .zshrc に追加して永続化することを推奨
            echo 'export PATH=$PATH:$ANDROID_HOME/platform-tools' >> ~/.zshrc
            source ~/.zshrc
            ```
        *   **Windows (Command Prompt):**
            ```cmd
            set PATH=%PATH%;%ANDROID_HOME%\platform-tools
            rem システムの環境変数設定から永続化することを推奨
            ```
        *   **Windows (PowerShell):**
            ```powershell
            $env:Path = "$env:Path;$env:ANDROID_HOME\platform-tools"
            # システムの環境変数設定から永続化することを推奨
            ```

### 1.3 Androidスマートフォンで開発者向けオプションとUSBデバッグを有効にする
コンピュータから直接スマートフォンにアプリをインストールするには、以下の設定が必要です。

**どこで作業するか:** Androidスマートフォン
**何を使って作業するか:** スマートフォンの設定アプリ

1.  **設定アプリを開く:**
    *   **Androidスマートフォン** で **設定** アプリのアイコンをタップして開きます。

2.  **開発者向けオプションを有効にする:**
    *   **設定** アプリ内で、下にスクロールして **端末情報** （または **デバイス情報**）をタップします。
    *   **ビルド番号** を見つけます。これは通常、「ソフトウェア情報」などのサブメニュー内にある場合があります。
    *   **ビルド番号** を7回連続で素早くタップします。「これでデベロッパーになりました！」というメッセージが表示されるはずです。

3.  **USBデバッグを有効にする:**
    *   **設定** に戻ると、新しいオプション **開発者向けオプション** が表示されます。これをタップします。
    *   **USBデバッグ** の項目を見つけて、トグルスイッチをタップして有効にします。

4.  **USB接続とデバッグの許可:**
    *   USBケーブルで **Androidスマートフォン** を **開発マシン** に接続します。
    *   スマートフォンに「USBデバッグを許可しますか？」というプロンプトが表示されたら、「常にこのコンピュータからのデバッグを許可する」にチェックを入れ、「許可」をタップします。
    *   **開発マシン** の **ターミナル** または **コマンドプロンプト** で `adb devices` と入力し、Enterキーを押します。接続されているデバイスのリストが表示され、スマートフォンのシリアル番号の横に `device` と表示されていれば、正しく接続されています。

## 2. Buildozerを使用したPython-for-Android (Py4A) のセットアップ

Buildozerは、PythonアプリケーションをAndroid向けにパッケージ化するプロセスを簡素化します。

### 2.1 Buildozerのインストール

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

1.  **ターミナル/コマンドプロンプトを開く:**
    *   **macOS/Linux:** アプリケーションフォルダから「ターミナル」を検索して開きます。
    *   **Windows:** スタートメニューで「cmd」と入力して「コマンドプロンプト」を開くか、「PowerShell」を検索して開きます。

2.  **Buildozerのインストールコマンドを実行:**
    *   開いたターミナル/コマンドプロンプトで以下のコマンドを入力し、Enterキーを押します。
        ```bash
        pip install buildozer
        ```
    *   インストールが完了するまで待ちます。

### 2.2 プロジェクトのBuildozerの初期化

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

1.  **プロジェクトディレクトリに移動:**
    *   ターミナル/コマンドプロンプトで、お小遣い帳アプリのプロジェクトのルートディレクトリ（`allowance.py` がある場所）に移動します。
        ```bash
        cd /Users/minamidenshiimanaka/AI/okodukai
        ```

2.  **Buildozerの初期化コマンドを実行:**
    *   以下のコマンドを入力し、Enterキーを押します。
        ```bash
        buildozer init
        ```
    *   このコマンドは、プロジェクトディレクトリに `buildozer.spec` ファイルを作成します。このファイルには、Androidアプリケーションのすべての設定が含まれています。

## 3. Android用Pythonアプリケーションの準備

現在の `allowance.py` はHTTPサーバーを実行します。Androidの場合、このサーバーを起動するメインのエントリポイントが必要です。

### 3.1 `main.py` の作成

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** テキストエディタ (例: VS Code, Sublime Text, Notepad++)

1.  **テキストエディタを開く:**
    *   **開発マシン** でお好みのテキストエディタ（VS Code, Sublime Text, Notepad++など）を開きます。

2.  **`main.py` ファイルを作成し保存:**
    *   新しいファイルを作成し、以下の内容を記述します。

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
    *   このファイルをプロジェクトのルートディレクトリ（`allowance.py` と同じ場所）に `main.py` という名前で保存します。

### 3.2 `buildozer.spec` の変更

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** テキストエディタ (例: VS Code, Sublime Text, Notepad++)

1.  **`buildozer.spec` ファイルを開く:**
    *   ステップ2.2で作成された `buildozer.spec` ファイルをテキストエディタで開きます。

2.  **以下の行を変更します。**
    *   **`title`**: アプリケーションのタイトルを設定します。Androidデバイスに表示されるアプリ名になります。
        ```ini
        title = お小遣い帳
        ```
    *   **`package.name`**: アプリケーションのユニークなパッケージ名を設定します。通常、逆ドメイン形式を使用します。
        ```ini
        package.name = allowanceapp
        ```
    *   **`package.domain`**: あなたのドメインを設定します。`package.name` と組み合わせてユニークなIDを形成します。
        ```ini
        package.domain = org.yourcompany
        ```
    *   **`source.dir`**: Pythonソースコードを含むディレクトリを指定します。現在のプロジェクトのルートディレクトリを指すように `.` に設定します。
        ```ini
        source.dir = .
        ```
    *   **`requirements`**: アプリケーションが必要とするPythonライブラリを指定します。`allowance.py` は標準ライブラリモジュールを使用しているため、`python3` で十分ですが、Buildozerの仕組み上 `kivy` が必要になることが多いです。
        ```ini
        requirements = python3,kivy
        ```
        *(注: Kivyは通常、Androidアプリを作成するためのBuildozerの基盤となるメカニズムによってデフォルトで含まれるか、必要とされます。UIにKivyを使用していなくても、Python環境のセットアップに役立ちます。)*
    *   **`android.api`**: ターゲットAndroid APIレベルを設定します。これはアプリが動作するAndroidのバージョンを示します。通常、最新の安定版または推奨されるAPIレベル（例: `27` またはそれ以上）を設定します。
        ```ini
        android.api = 27
        ```
    *   **`android.minapi`**: サポートされる最小Android APIレベルを設定します。これより古いAndroidバージョンではアプリは動作しません。
        ```ini
        android.minapi = 21
        ```
    *   **`android.permissions`**: アプリケーションが必要とするAndroidのパーミッションを追加します。Webサーバーを実行するためにはインターネットアクセスが必要です。
        ```ini
        android.permissions = INTERNET
        ```
    *   **`fullscreen`**: アプリケーションをフルスクリーンで表示するかどうかを設定します。標準のアプリウィンドウが必要な場合は `0`、フルスクリーンの場合は `1` に設定します。
        ```ini
        fullscreen = 0
        ```
    *   **`orientation`**: アプリケーションの画面の向きを設定します（`landscape` または `portrait`）。
        ```ini
        orientation = portrait
        ```

    **重要な点として、Webサーバーアプリの場合、`allowance.py` と `main.py` （およびアプリの初期状態の一部であるCSVファイル）を含めるようにBuildozerに指示する必要があります。**
    *   **`source.include_exts`**: `.py` が含まれていることを確認します。
    *   **`source.exclude_dirs`**: `.git`, `.buildozer` などのビルドに不要なディレクトリを除外します。
    *   **`source.include_patterns`**: ここにCSVファイルを追加します。`allowance.csv`, `goals.csv`, `presets.csv` が含まれていることを確認してください。
        ```ini
        source.include_patterns = *.py,*.png,*.jpg,*.kv,*.atlas,*.csv
        ```

## 4. Androidアプリケーション (APK) のビルド

`buildozer.spec` が設定されたら、Androidアプリケーションをビルドできます。

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

1.  **プロジェクトディレクトリに移動:**
    *   ターミナル/コマンドプロンプトで、お小遣い帳アプリのプロジェクトのルートディレクトリに移動していることを確認します。

### 4.1 以前のビルドのクリーンアップ (オプションですが推奨)
    *   以下のコマンドを入力し、Enterキーを押します。これにより、以前のビルドアーティファクトが削除され、クリーンな状態からビルドが開始されます。
        ```bash
        buildozer clean
        ```

### 4.2 デバッグAPKのビルド
    *   以下のコマンドを入力し、Enterキーを押します。
        ```bash
        buildozer android debug
        ```
    *   このコマンドは、必要なAndroid SDKコンポーネント、NDK、Python-for-Androidツールチェーンをダウンロードし、PythonコードをコンパイルしてAPKファイルにパッケージ化します。**このプロセスは、ビルド環境全体をセットアップするため、初回実行時にはかなりの時間（数十分から数時間）かかる場合があります。** 途中で止まっているように見えても、辛抱強く待ってください。

    *   生成されたAPKファイルは、プロジェクト内の `bin/` ディレクトリに配置されます（例: `bin/allowanceapp-0.1-debug.apk`）。

## 5. Androidデバイスへのインストールと実行

### 5.1 APKのインストール

**どこで作業するか:** 開発マシン (PC/Mac/Linux)
**何を使って作業するか:** ターミナル/コマンドプロンプト

1.  **Androidスマートフォンの接続確認:**
    *   **Androidスマートフォン** がUSB経由で **開発マシン** に接続され、USBデバッグが有効になっていることを確認します。
    *   **開発マシン** の **ターミナル** または **コマンドプロンプト** で `adb devices` と入力し、Enterキーを押します。接続されているデバイスのリストが表示され、スマートフォンのシリアル番号の横に `device` と表示されていれば、正しく接続されています。

2.  **APKのインストールコマンドを実行:**
    *   以下のコマンドを入力し、Enterキーを押します。
        ```bash
        adb install bin/allowanceapp-0.1-debug.apk
        ```
    *   `allowanceapp-0.1-debug.apk` を、ステップ4.2で生成されたAPKファイルの実際の名前で置き換えてください。
    *   インストールが成功すると、「Success」というメッセージが表示されます。

### 5.2 アプリケーションの実行

**どこで作業するか:** Androidスマートフォン
**何を使って作業するか:** スマートフォンのホーム画面またはアプリドロワー

1.  **アプリのアイコンを見つける:**
    *   **Androidスマートフォン** のホーム画面またはアプリドロワー（アプリ一覧）に、「お小遣い帳」アプリのアイコンが表示されているはずです。

2.  **アプリを起動する:**
    *   アイコンをタップしてアプリケーションを起動します。

アプリは内部でPython HTTPサーバーを起動します。この時点では、アプリ自体は空の画面が表示されるかもしれません。Pythonスクリプトによって提供されるWebインターフェースを表示するには、Androidアプリ内にWebViewを実装する必要があります。このガイドは、PythonサーバーをAndroidで実行することに焦点を当てています。WebViewとの統合は、Android開発の次のステップになります。

**WebView統合に関する注意:**
上記の `main.py` は単にPythonサーバーを起動するだけです。完全なAndroidアプリでは、通常、Java/KotlinアクティビティがWebViewを作成し、`http://127.0.0.1:8000` （またはPythonサーバーが実行されているポート）を指すようにします。これには、より高度なAndroid開発の知識が必要です。Java/Kotlinを記述せずに、より統合されたエクスペリエンスが必要な場合は、KivyのWebView機能やその他のPythonベースのAndroid用UIフレームワークを検討することもできます。

この最初のデプロイの目標は、PythonサーバーをAndroidで実行することです。その後、Androidデバイスのブラウザで `http://127.0.0.1:8000` にアクセスすることで（アプリがバックグラウンド実行を許可し、ポートがアクセス可能な場合）、アクセスできます。ただし、専用のWebViewがローカルWebアプリを統合する標準的な方法です。
