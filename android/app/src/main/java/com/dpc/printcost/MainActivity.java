package com.dpc.printcost;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.print.PrintAttributes;
import android.print.PrintDocumentAdapter;
import android.print.PrintManager;
import android.provider.MediaStore;
import android.util.Base64;
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

  /** 把 PNG 长图（base64）写入系统「图片」目录（Android 10+ 走 MediaStore Pictures）。 */
  private boolean saveBitmapToPictures(String filename, String base64) {
    byte[] bytes;
    try {
      bytes = Base64.decode(base64, Base64.DEFAULT);
    } catch (Exception e) {
      toast("图片数据无效"); return false;
    }
    String safe = sanitize(filename);
    try {
      if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
        ContentValues cv = new ContentValues();
        cv.put(MediaStore.Images.Media.DISPLAY_NAME, safe);
        cv.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        cv.put(MediaStore.Images.Media.IS_PENDING, 1);
        ContentResolver cr = getContentResolver();
        Uri uri = cr.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv);
        if (uri == null) { toast("保存失败"); return false; }
        try (OutputStream os = cr.openOutputStream(uri)) {
          if (os == null) { toast("保存失败"); return false; }
          os.write(bytes); os.flush();
        }
        cv.clear(); cv.put(MediaStore.Images.Media.IS_PENDING, 0);
        cr.update(uri, cv, null, null);
        toast("长图已保存到「图片」：" + safe);
      } else {
        File dir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        if (dir == null) dir = new File(getFilesDir(), "Pictures");
        if (!dir.exists() && !dir.mkdirs()) { toast("保存失败"); return false; }
        File out = new File(dir, safe);
        try (FileOutputStream fo = new FileOutputStream(out)) {
          fo.write(bytes); fo.flush();
        }
        toast("长图已保存：" + out.getAbsolutePath());
      }
      return true;
    } catch (Exception e) {
      Log.w(TAG, "saveBitmap failed: " + e);
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

  /* ===== 在线升级：DownloadManager 下载 Release APK → 拉起系统安装器 ===== */

  private void startUpdate(String url, String version) {
    try {
      DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
      if (dm == null) { toast("无法下载更新"); return; }
      String ver = cleanVersion(version);
      DownloadManager.Request req = new DownloadManager.Request(Uri.parse(url));
      req.setMimeType("application/vnd.android.package-archive");
      req.setTitle(getString(R.string.app_name) + (ver.isEmpty() ? " 更新包" : " v" + ver + " 更新包"));
      req.setDescription(ver.isEmpty() ? "正在下载新版本安装包…" : "正在下载新版本 v" + ver + "…");
      req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
      req.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "print-cost-update.apk");
      long id = dm.enqueue(req);
      toast(ver.isEmpty() ? "开始下载新版本…" : "开始下载 v" + ver + "…");
      pollDownload(dm, id, 0);
    } catch (Exception e) {
      Log.w(TAG, "update failed: " + e);
      toast("下载失败：" + e.getMessage());
    }
  }

  /** 规整前端传来的版本号：去掉前缀 v、空白与 WebView 传 undefined/null 的兜底。 */
  private static String cleanVersion(String version) {
    if (version == null) return "";
    String v = version.trim();
    if (v.isEmpty() || "undefined".equalsIgnoreCase(v) || "null".equalsIgnoreCase(v)) return "";
    if (v.startsWith("v") || v.startsWith("V")) v = v.substring(1).trim();
    return v.replaceAll("[^0-9A-Za-z._-]", "");
  }

  /** 轮询下载状态（避免广播接收器在 targetSdk 34+ 上的注册限制），每秒一次，最长 10 分钟。 */
  private void pollDownload(DownloadManager dm, long id, int tries) {
    final int MAX_TRIES = 600;
    new Handler(Looper.getMainLooper()).postDelayed(() -> {
      try (Cursor c = dm.query(new DownloadManager.Query().setFilterById(id))) {
        if (c != null && c.moveToFirst()) {
          int status = c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
          if (status == DownloadManager.STATUS_SUCCESSFUL) {
            Uri uri = dm.getUriForDownloadedFile(id);
            toast("下载完成，准备安装…");
            installApk(uri);
            return;
          }
          if (status == DownloadManager.STATUS_FAILED) {
            toast("下载失败，请到 GitHub 发布页手动下载");
            return;
          }
        }
      } catch (Exception e) {
        Log.w(TAG, "poll download failed: " + e);
      }
      if (tries < MAX_TRIES) pollDownload(dm, id, tries + 1);
    }, 1000);
  }

  private void installApk(Uri uri) {
    try {
      Intent i = new Intent(Intent.ACTION_VIEW);
      i.setDataAndType(uri, "application/vnd.android.package-archive");
      i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
      startActivity(i);
    } catch (ActivityNotFoundException | SecurityException e) {
      Log.w(TAG, "install failed: " + e);
      toast("无法启动安装：" + e.getMessage() + "（可能未允许「安装未知应用」）");
    }
  }

  /** 拉起系统打印对话框（打印机列表里可选「保存为 PDF」）。 */
  private void startPrint() {    try {
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

    /** 检查更新后由前端调用：url 为 GitHub Release 的 APK 下载地址，version 为新版本号（用于下载通知文案）。 */
    @JavascriptInterface
    public boolean updateApp(String url, String version) {
      if (url == null || !url.startsWith("https://")) return false;
      runOnUiThread(() -> startUpdate(url, version));
      return true;
    }

    /** 报价长图保存：前端 Canvas 生成 PNG，base64 传入，写入系统「图片」目录。 */
    @JavascriptInterface
    public boolean saveBitmap(String filename, String base64) {
      if (base64 == null || base64.isEmpty()) return false;
      return saveBitmapToPictures(filename, base64);
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
