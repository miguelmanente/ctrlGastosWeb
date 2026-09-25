import threading
import time
from kivy.app import App
from kivy.clock import Clock
from jnius import autoclass, cast

from app import app as flask_app

# Clases nativas de Android
PythonActivity = autoclass('org.kivy.android.PythonActivity')
WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')

def start_flask():
    flask_app.run(host="127.0.0.1", port=5000, debug=False)

class ControlGastosApp(App):
    def build(self):
        # Inicia Flask en segundo plano
        threading.Thread(target=start_flask, daemon=True).start()
        
        # Obtenemos la actividad de Android
        activity = PythonActivity.mActivity
        webview = WebView(activity)
        webview.getSettings().setJavaScriptEnabled(True)
        webview.setWebViewClient(WebViewClient())
        webview.loadUrl("http://127.0.0.1:5000")
        
        activity.setContentView(webview)

if __name__ == "__main__":
    ControlGastosApp().run()