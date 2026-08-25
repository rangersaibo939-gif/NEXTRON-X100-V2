from pathlib import Path


def make_interactive(project_root: str) -> Path:
    """Add useful local interactions to the generated NEXTRON Compose console."""
    source = next(Path(project_root).glob("app/src/main/java/**/MainActivity.kt"))
    text = source.read_text(encoding="utf-8")

    text = text.replace(
        "import androidx.compose.material3.MaterialTheme\n",
        "import androidx.compose.material3.MaterialTheme\nimport androidx.compose.material3.OutlinedTextField\n",
    )
    text = text.replace(
        '    var lastAction by remember { mutableStateOf("") }\n',
        '    var lastAction by remember { mutableStateOf("") }\n'
        '    var taskRequest by remember { mutableStateOf("") }\n',
    )
    text = text.replace(
        '                Spacer(modifier = Modifier.height(20.dp))\n                when (currentScreen) {',
        '                Spacer(modifier = Modifier.height(12.dp))\n'
        '                OutlinedTextField(\n'
        '                    value = taskRequest,\n'
        '                    onValueChange = { taskRequest = it },\n'
        '                    modifier = Modifier.fillMaxWidth(),\n'
        '                    label = { Text("What should NEXTRON build?") },\n'
        '                    placeholder = { Text("Example: Create an expense tracker") },\n'
        '                )\n'
        '                Spacer(modifier = Modifier.height(20.dp))\n'
        '                when (currentScreen) {',
    )

    replacements = {
        'Button(onClick = { lastAction = "Create App"; actionCount++ }) { Text("Create App") }':
            'Button(onClick = {\n'
            '    lastAction = if (taskRequest.isBlank()) "Enter an app request first" else "App request captured: $taskRequest"\n'
            '    actionCount++\n'
            '}) { Text("Create App") }',
        'Button(onClick = { lastAction = "Run Agent"; actionCount++ }) { Text("Run Agent") }':
            'Button(onClick = {\n'
            '    lastAction = if (taskRequest.isBlank()) "Create an app request first" else "Multi-brain plan ready: Planner → Coder → Reviewer"\n'
            '    actionCount++\n'
            '}) { Text("Run Agent") }',
        'Button(onClick = { lastAction = "Build APK"; actionCount++ }) { Text("Build APK") }':
            'Button(onClick = {\n'
            '    lastAction = "Build requested — use the GitHub Actions APK pipeline"\n'
            '    actionCount++\n'
            '}) { Text("Build APK") }',
        'Button(onClick = { lastAction = "Download APK"; actionCount++ }) { Text("Download APK") }':
            'Button(onClick = {\n'
            '    lastAction = "APK artifact is available from the latest GitHub Actions run"\n'
            '    actionCount++\n'
            '}) { Text("Download APK") }',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    source.write_text(text, encoding="utf-8")
    return source
