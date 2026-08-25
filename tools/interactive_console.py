from pathlib import Path


def make_interactive(project_root: str) -> Path:
    """Add useful local interactions to the generated NEXTRON Compose console."""
    source = next(Path(project_root).glob("app/src/main/java/**/MainActivity.kt"))
    text = source.read_text(encoding="utf-8")
    text = text.replace(
        "import android.os.Bundle\n",
        "import android.os.Bundle\nimport android.content.Intent\nimport android.net.Uri\n",
    )
    text = text.replace(
        "import androidx.compose.material3.MaterialTheme\n",
        "import androidx.compose.material3.MaterialTheme\nimport androidx.compose.material3.OutlinedTextField\nimport androidx.compose.ui.platform.LocalContext\n",
    )
    text = text.replace(
        '    var lastAction by remember { mutableStateOf("") }\n',
        '    var lastAction by remember { mutableStateOf("") }\n    var taskRequest by remember { mutableStateOf("") }\n    val context = LocalContext.current\n',
    )
    text = text.replace(
        '                Spacer(modifier = Modifier.height(20.dp))\n                when (currentScreen) {',
        '                Spacer(modifier = Modifier.height(12.dp))\n                OutlinedTextField(\n                    value = taskRequest,\n                    onValueChange = { taskRequest = it },\n                    modifier = Modifier.fillMaxWidth(),\n                    label = { Text("What should NEXTRON build?") },\n                    placeholder = { Text("Example: Create an expense tracker") },\n                )\n                Spacer(modifier = Modifier.height(20.dp))\n                when (currentScreen) {',
    )
    replacements = {
        'Button(onClick = { lastAction = "Create App"; actionCount++ }) { Text("Create App") }': 'Button(onClick = { lastAction = if (taskRequest.isBlank()) "Enter an app request first" else "App request captured: $taskRequest"; actionCount++ }) { Text("Create App") }',
        'Button(onClick = { lastAction = "Run Agent"; actionCount++ }) { Text("Run Agent") }': 'Button(onClick = { lastAction = if (taskRequest.isBlank()) "Create an app request first" else "Multi-brain plan ready: Planner → Coder → Reviewer"; actionCount++ }) { Text("Run Agent") }',
        'Button(onClick = { lastAction = "Build APK"; actionCount++ }) { Text("Build APK") }': 'Button(onClick = { lastAction = "Opening GitHub Actions — tap Run workflow"; context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/rangersaibo939-gif/NEXTRON-X100-V2/actions/workflows/nextron-builder-v2.yml"))); actionCount++ }) { Text("Build APK") }',
        'Button(onClick = { lastAction = "Download APK"; actionCount++ }) { Text("Download APK") }': 'Button(onClick = { lastAction = "Opening GitHub Actions artifacts"; context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/rangersaibo939-gif/NEXTRON-X100-V2/actions"))); actionCount++ }) { Text("Download APK") }',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    source.write_text(text, encoding="utf-8")
    return source
