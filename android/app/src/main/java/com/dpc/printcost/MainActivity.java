package com.dpc.printcost;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.provider.MediaStore;
import android.util.Log;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import androidx.webkit.WebViewAssetLoader;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

/**
 * 3D 打印成本计算器 —— 单 WebView 壳。
 *
 * 页面以 assets/index.html 形式打包进 APK，通过 WebViewAssetLoader 映射到
 * https://appassets.androidplatform.net/assets/index.html，从而获得正常 Web 源，
 * localStorage（参数 / 预设 / 分类）才能可靠持久化。
 *
 * 导出链路：WebView 默认【不处理】<a download> + Blob 下载，且页面非 iframe，
 * 前端的 isEmbedded() 兜底不会触发 —— 表现为「点导出/备份毫无反应」。
 * 因此这里注入 window.AndroidBridge.saveText()，由前端优先调用，写入系统「下载」目录。
 */
public class MainActivity extends Activity {

  private static final String TAG = "DPC";
  private static final String ORIGIN = "https://appassets.androidplatform.net";
  private static final String START_URL = ORIGIN + "/assets/index.html";
  private static final int REQ_FILE_CHOOSER = 1001;

  private WebView web;
  private ValueCallback<Uri[]> filePathCallback;

  @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
  @Override
  protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);

    FrameLayout root = new FrameLayout(this);
    root.setLayoutParams(new ViewGroup.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

    web = new WebView(this);
    web.setLayoutParams(new FrameLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
    web.setBackgroundColor(0xFFF4F5F8);
    web.setOverScrollMode(WebView.OVER_SCROLL_NEVER);
    root.addView(web);
    setContentView(root);

    WebSettings ws = web.getSettings();
    ws.setJavaScriptEnabled(true);
    ws.setDomStorageEnabled(true);      // localStorage：参数与预设持久化的前提
    ws.setDatabaseEnabled(true);
    ws.setAllowFileAccess(false);       // 页面走 https 映射，不需要 file:// 访问
    ws.setAllowContentAccess(false);
    ws.setSupportZoom(false);
    ws.setBuiltInZoomControls(false);
    ws.setDisplayZoomControls(false);
    ws.setTextZoom(100);
    ws.setMediaPlaybackRequiresUserGesture(true);
    ws.setCacheMode(WebSettings.LOAD_DEFAULT);

    // 导出 / 备份的原生保存桥（前端在 download() 中优先调用）
    web.addJavascriptInterface(new JsBridge(), "AndroidBridge");

    final WebViewAssetLoader loader = new WebViewAssetLoader.Builder()
        .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
        .build();

    web.setWebViewClient(new WebViewClient() {
      @Override
      public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
        return loader.shouldInterceptRequest(request.getUrl());
      }

      @Override
      public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
        Uri u = request.getUrl();
        if (u != null && ORIGIN.equals(u.getScheme() + "://" + u.getHost())) return false;
        // 非本地页面（例如导出面板里的链接）交给系统浏览器
        if (u != null && ("http".equals(u.getScheme()) || "https".equals(u.getScheme()))) {
          try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
          } catch (ActivityNotFoundException ignored) {
          }
        }
        return true;
      }
    });

    // 打印 / 另存为 PDF、对话框、以及「恢复备份 / 导入预设」的文件选择
    web.setWebChromeClient(new WebChromeClient() {
      @Override
      public boolean onJsAlert(WebView view, String url, String message,
                               final android.webkit.JsResult result) {
        new android.app.AlertDialog.Builder(MainActivity.this)
            .setMessage(message)
            .setPositiveButton(android.R.string.ok, (d, w) -> result.confirm())
            .setOnCancelListener(d -> result.cancel())
            .show();
        return true;
      }

      @Override
      public boolean onJsConfirm(WebView view, String url, String message,
                                 final android.webkit.JsResult result) {
        new android.app.AlertDialog.Builder(MainActivity.this)
            .setMessage(message)
            .setPositiveButton(android.R.string.ok, (d, w) -> result.confirm())
            .setNegativeButton(android.R.string.cancel, (d, w) -> result.cancel())
            .setOnCancelListener(d -> result.cancel())
            .show();
        return true;
      }

      /* 让 <input type="file"> 能弹出系统文件选择器（恢复备份 / 导入预设必需） */
      @Override
      public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                       FileChooserParams params) {
        if (filePathCallback != null) {
          filePathCallback.onReceiveValue(null);
        }
        filePathCallback = callback;
        try {
          Intent intent = params.createIntent();
          intent.addCategory(Intent.CATEGORY_OPENABLE);
          startActivityForResult(intent, REQ_FILE_CHOOSER);
          return true;
        } catch (ActivityNotFoundException | SecurityException e) {
          filePathCallback = null;
          toast("无法打开文件选择器");
          return false;
        }
      }
    });

    if (savedInstanceState != null) {
      web.restoreState(savedInstanceState);
    } else {
      web.loadUrl(START_URL);
    }
  }

  @Override
  protected void onActivityResult(int requestCode, int resultCode, Intent data) {
    if (requestCode == REQ_FILE_CHOOSER) {
      if (filePathCallback != null) {
        filePathCallback.onReceiveValue(
            WebChromeClient.FileChooserParams.parseResult(resultCode, data));
        filePathCallback = null;
      }
      return;
    }
    super.onActivityResult(requestCode, resultCode, data);
  }

  /** 把导出内容写入系统「下载」目录，并给出可见反馈。 */
  private boolean saveTextToDownloads(String filename, String mime, String content) {
    String safe = sanitize(filename);
    byte[] bytes = content.getBytes(StandardCharsets.UTF_8);
    try {
      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        ContentValues cv = new ContentValues();
        cv.put(MediaStore.Downloads.DISPLAY_NAME, safe);
        cv.put(MediaStore.Downloads.MIME_TYPE, mime == null ? "application/octet-stream" : mime);
        cv.put(MediaStore.Downloads.IS_PENDING, 1);
        ContentResolver cr = getContentResolver();
        Uri uri = cr.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, cv);
        if (uri == null) return false;
        try (OutputStream os = cr.openOutputStream(uri)) {
          if (os == null) return false;
          os.write(bytes);
          os.flush();
        }
        cv.clear();
        cv.put(MediaStore.Downloads.IS_PENDING, 0);
        cr.update(uri, cv, null, null);
        toast("已保存到「下载」：" + safe);
      } else {
        // API 24–28：应用专属目录无需运行时权限，且仍可被文件管理器看到
        File dir = getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
        if (dir == null) dir = new File(getFilesDir(), "Download");
        if (!dir.exists() && !dir.mkdirs()) return false;
        File out = new File(dir, safe);
        try (FileOutputStream fo = new FileOutputStream(out)) {
          fo.write(bytes);
          fo.flush();
        }
        toast("已保存：" + out.getAbsolutePath());
      }
      return true;
    } catch (Exception e) {
      Log.w(TAG, "saveText failed: " + e);
      toast("保存失败：" + e.getMessage());
      return false;
    }
  }

  private static String sanitize(String name) {
    String s = (name == null || name.trim().isEmpty()) ? "export.txt" : name.trim();
    s = s.replace('\\', '_').replace('/', '_').replace(':', '_')
         .replace('*', '_').replace('?', '_').replace('"', '_')
         .replace('<', '_').replace('>', '_').replace('|', '_');
    return s;
  }

  /** 拉起系统打印对话框（打印机列表里可选「保存为 PDF」）。 */
  private void startPrint() {
    try {
      PrintManager pm = (PrintManager) getSystemService(Context.PRINT_SERVICE);
      if (pm == null || web == null) {
        toast("当前设备不支持打印");
        return;
      }
      String jobName = getString(R.string.app_name) + " - 3D打印成本报价单";
      PrintDocumentAdapter adapter = web.createPrintDocumentAdapter(jobName);
      pm.print(jobName, adapter, new PrintAttributes.Builder()
          .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
          .build());
    } catch (Exception e) {
      Log.w(TAG, "print failed: " + e);
      toast("无法启动打印：" + e.getMessage());
    }
  }

  private void toast(final String msg) {
    runOnUiThread(() -> Toast.makeText(getApplicationContext(), msg, Toast.LENGTH_LONG).show());
  }

  /** 暴露给网页的原生桥。注意：方法运行在 WebView 的 JavaBridge 线程，UI 操作需切回主线程。 */
  private class JsBridge {
    @JavascriptInterface
    public boolean saveText(String filename, String mime, String content) {
      return saveTextToDownloads(filename, mime, content == null ? "" : content);
    }

    /** 打印 / 另存为 PDF。WebView 不支持 window.print()，必须由原生发起打印任务。 */
    @JavascriptInterface
    public boolean printPage() {
      runOnUiThread(MainActivity.this::startPrint);
      return true;
    }

    /** 供前端探测桥是否可用 */
    @JavascriptInterface
    public boolean available() {
      return true;
    }
  }

  @Override
  protected void onSaveInstanceState(Bundle outState) {
    super.onSaveInstanceState(outState);
    if (web != null) web.saveState(outState);
  }

  @SuppressWarnings("deprecation")
  @Override
  public void onBackPressed() {
    if (filePathCallback != null) {
      filePathCallback.onReceiveValue(null);
      filePathCallback = null;
      return;
    }
    if (web != null && web.canGoBack()) {
      web.goBack();
    } else {
      super.onBackPressed();
    }
  }

  @Override
  protected void onDestroy() {
    if (web != null) {
      web.destroy();
      web = null;
    }
    super.onDestroy();
  }
}
