from pathlib import Path


def fix_generated_dashboard(root: str) -> None:
    source = Path(root) / "app" / "src" / "main" / "java" / "com" / "nextron" / "x100" / "MainActivity.kt"
    if not source.exists():
        return

    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "import androidx.compose.foundation.layout.Row\n",
        "import androidx.compose.foundation.layout.Row\n"
        "import androidx.compose.foundation.layout.imePadding\n"
        "import androidx.compose.foundation.rememberScrollState\n"
        "import androidx.compose.foundation.verticalScroll\n",
    )
    text = text.replace(
        "                    .verticalScroll(scrollState)\n                    .padding(16.dp)",
        "                    .verticalScroll(scrollState)\n                    .padding(16.dp)\n                    .imePadding()",
    )

    manifest = Path(root) / "app" / "src" / "main" / "AndroidManifest.xml"
    if manifest.exists():
        manifest_text = manifest.read_text(encoding="utf-8")
        manifest_text = manifest_text.replace(
            '<activity android:name=".MainActivity" android:exported="true">',
            '<activity android:name=".MainActivity" android:exported="true" android:windowSoftInputMode="adjustResize">',
        )
        manifest.write_text(manifest_text, encoding="utf-8")

    source.write_text(text, encoding="utf-8")
