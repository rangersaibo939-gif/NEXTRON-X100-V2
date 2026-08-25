from pathlib import Path


def fix_generated_dashboard(root: str) -> None:
    source = Path(root) / "app" / "src" / "main" / "java" / "com" / "nextron" / "x100" / "MainActivity.kt"
    if not source.exists():
        return
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "import androidx.compose.foundation.layout.Row\n",
        "import androidx.compose.foundation.layout.Row\n"
        "import androidx.compose.foundation.rememberScrollState\n"
        "import androidx.compose.foundation.verticalScroll\n",
    )
    text = text.replace(
        "Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {",
        "Column(modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {",
    )
    source.write_text(text, encoding="utf-8")
