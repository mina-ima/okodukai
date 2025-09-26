# Android Deployment Guide for お小遣い帳 (Allowance App)

This guide will walk you through the steps to deploy your Python-based Allowance App to an Android smartphone using Python-for-Android (Py4A) and Buildozer.

## 1. Prerequisites

Before you begin, ensure you have the following installed and configured on your development machine:

### 1.1 Java Development Kit (JDK)
Android development requires a JDK.
- Download and install the latest LTS version of Oracle JDK or OpenJDK (e.g., JDK 11 or JDK 17).
- Set the `JAVA_HOME` environment variable to your JDK installation directory.

### 1.2 Android Studio
Android Studio provides the Android SDK, platform tools, and an emulator (optional but recommended for testing).
- Download and install [Android Studio](https://developer.android.com/studio).
- During installation, ensure you install the Android SDK and at least one Android Platform (e.g., Android 10.0 or higher).
- Configure the `ANDROID_HOME` environment variable to point to your Android SDK installation directory (usually `~/Android/sdk` on Linux/macOS or `%LOCALAPPDATA%\Android\sdk` on Windows).
- Add the Android SDK platform tools to your system's PATH. For example, on Linux/macOS:
  ```bash
  export PATH=$PATH:$ANDROID_HOME/platform-tools
  ```

### 1.3 Enable Developer Options and USB Debugging on your Android Phone
To install apps directly from your computer to your phone:
1.  Go to your phone's **Settings**.
2.  Scroll down and tap **About phone** (or **About device**).
3.  Find **Build number** and tap it 7 times rapidly. You should see a message "You are now a developer!"
4.  Go back to **Settings**, and you should see a new option: **Developer options**.
5.  Tap **Developer options**.
6.  Enable **USB debugging**.
7.  Connect your phone to your computer via a USB cable. When prompted on your phone, allow USB debugging from your computer.

## 2. Set up Python-for-Android (Py4A) with Buildozer

Buildozer simplifies the process of packaging Python applications for Android.

### 2.1 Install Buildozer
Open your terminal or command prompt and install Buildozer:
```bash
pip install buildozer
```

### 2.2 Initialize Buildozer for your project
Navigate to your project's root directory (where `allowance.py` is located):
```bash
cd /Users/minamidenshiimanaka/AI/okodukai
```
Run Buildozer initialization:
```bash
buildozer init
```
This command will create a `buildozer.spec` file in your project directory. This file contains all the configuration for your Android application.

## 3. Prepare the Python Application for Android

The current `allowance.py` runs an HTTP server. For Android, we need a main entry point that starts this server.

### 3.1 Create `main.py`
Create a new file named `main.py` in your project's root directory with the following content:

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

### 3.2 Modify `buildozer.spec`
Open the `buildozer.spec` file that was created in step 2.2. You'll need to modify several lines:

-   **`title`**: Your application's title (e.g., `お小遣い帳`).
-   **`package.name`**: A unique package name (e.g., `org.you.allowanceapp`).
-   **`package.domain`**: Your domain (e.g., `org.you`).
-   **`source.dir`**: The directory containing your Python source code. For this project, it should be `.` (current directory).
-   **`requirements`**: Add `python3`, `kivy` (Buildozer often uses Kivy for UI, even if you're just running a server, it provides the Python environment), `requests` (if your app uses it, though `allowance.py` uses `http.server`), and any other Python libraries your `allowance.py` depends on. For `allowance.py`, `python3` should be sufficient as it uses standard library modules.
    ```ini
    requirements = python3,kivy
    ```
    *(Note: Kivy is often included by default or required by Buildozer's underlying mechanisms for creating an Android app. Even if you're not using Kivy for UI, it helps set up the Python environment.)*
-   **`android.api`**: The target Android API level (e.g., `27` or higher).
-   **`android.minapi`**: The minimum Android API level supported (e.g., `21`).
-   **`android.permissions`**: Add necessary permissions. For a web server, you'll need internet access.
    ```ini
    android.permissions = INTERNET
    ```
-   **`fullscreen`**: Set to `0` if you want a standard app window, `1` for fullscreen.
-   **`orientation`**: `landscape` or `portrait`.

**Crucially, for a web server app, you'll need to tell Buildozer to include your `allowance.py` and `main.py` (and any CSV files if they are part of the app's initial state).**
-   **`source.include_exts`**: Ensure `.py` is included.
-   **`source.exclude_dirs`**: Exclude `.git`, `.buildozer`, etc.
-   **`source.include_patterns`**: Add your CSV files here.
    ```ini
    source.include_patterns = *.py,*.png,*.jpg,*.kv,*.atlas,*.csv
    ```
    Make sure `allowance.csv`, `goals.csv`, `presets.csv` are included.

## 4. Build the Android Application (APK)

With `buildozer.spec` configured, you can now build your Android application.

### 4.1 Clean previous builds (optional but recommended)
```bash
buildozer clean
```

### 4.2 Build the debug APK
```bash
buildozer android debug
```
This command will download necessary Android SDK components, NDK, Python-for-Android toolchains, compile your Python code, and package it into an APK file. This process can take a significant amount of time (tens of minutes to hours) on the first run, as it sets up the entire build environment.

The generated APK file will be located in the `bin/` directory within your project (e.g., `bin/allowanceapp-0.1-debug.apk`).

## 5. Install and Run on Android Device

### 5.1 Install the APK
Ensure your Android phone is connected to your computer via USB and USB debugging is enabled.
```bash
"adb install bin/allowanceapp-0.1-debug.apk"
```
Replace `allowanceapp-0.1-debug.apk` with the actual name of your generated APK file.

### 5.2 Run the Application
Once installed, you should see the "お小遣い帳" app icon on your phone's home screen or app drawer. Tap it to launch the application.

The app will start the Python HTTP server internally. You might need to implement a WebView within the Android app to display the web interface served by your Python script. This guide focuses on getting the Python server running on Android. Integrating it with a WebView would be the next step in Android development.

**Note on WebView Integration:**
The `main.py` provided above simply starts the Python server. A full Android app would typically have a Java/Kotlin activity that creates a WebView and points it to `http://127.0.0.1:8000` (or whatever port your Python server runs on). This requires more advanced Android development knowledge. For a simpler approach, you might look into Kivy's WebView capabilities or other Python-based UI frameworks for Android if you want a more integrated experience without writing Java/Kotlin.

For this initial deployment, the goal is to get the Python server running on Android. You can then access it via a browser on the Android device by navigating to `http://127.0.0.1:8000` (if the app allows background execution and the port is accessible). However, a dedicated WebView is the standard way to integrate a local web app.
