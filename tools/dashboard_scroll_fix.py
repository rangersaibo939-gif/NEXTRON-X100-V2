from pathlib import Path

p = Path("core/app_builder/project_generator.py")
s = p.read_text()
s = s.replace('import androidx.compose.foundation.layout.Row\n', 'import androidx.compose.foundation.layout.Row\nimport androidx.compose.foundation.rememberScrollState\nimport androidx.compose.foundation.verticalScroll\n')
s = s.replace('            Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {', '            Column(\n                modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())\n            ) {')
p.write_text(s)
