"""Minimal Android project generator used by NEXTRON Builder v2.

The generator intentionally produces a small, dependency-free Java Android
project first. Kotlin/Compose generation is a separate backend so the direct
on-device builder can remain deterministic and easy to diagnose.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GeneratedProject:
    root: Path
    package_name: str
    activity_class: str


class AndroidProjectGenerator:
    def generate(self, root: str, package_name: str, app_name: str = "NEXTRON App") -> GeneratedProject:
        target = Path(root)
        package_path = Path(*package_name.split("."))
        source_dir = target / "src" / "main" / "java" / package_path
        resource_dir = target / "src" / "main" / "res" / "values"
        source_dir.mkdir(parents=True, exist_ok=True)
        resource_dir.mkdir(parents=True, exist_ok=True)

        activity = "MainActivity"
        (source_dir / f"{activity}.java").write_text(
            "package " + package_name + ";\n\n"
            "import android.app.Activity;\n"
            "import android.os.Bundle;\n"
            "import android.widget.Button;\n"
            "import android.widget.TextView;\n"
            "import android.widget.LinearLayout;\n\n"
            "public class MainActivity extends Activity {\n"
            "  private int count = 0;\n"
            "  @Override public void onCreate(Bundle state) {\n"
            "    super.onCreate(state);\n"
            "    LinearLayout layout = new LinearLayout(this);\n"
            "    layout.setOrientation(LinearLayout.VERTICAL);\n"
            "    TextView title = new TextView(this);\n"
            f"    title.setText(\"{app_name}\");\n"
            "    Button button = new Button(this);\n"
            "    button.setText(\"Count: 0\");\n"
            "    button.setOnClickListener(v -> button.setText(\"Count: \" + (++count)));\n"
            "    layout.addView(title); layout.addView(button); setContentView(layout);\n"
            "  }\n"
            "}\n",
            encoding="utf-8",
        )
        (resource_dir / "strings.xml").write_text(
            "<resources><string name=\"app_name\">" + app_name + "</string></resources>\n",
            encoding="utf-8",
        )
        (target / "AndroidManifest.xml").write_text(
            "<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\">\n"
            f"  <application android:theme=\"@android:style/Theme.Material.Light.NoActionBar\" android:label=\"{app_name}\">\n"
            "    <activity android:name=\"." + activity + "\" android:exported=\"true\">\n"
            "      <intent-filter>\n"
            "        <action android:name=\"android.intent.action.MAIN\"/>\n"
            "        <category android:name=\"android.intent.category.LAUNCHER\"/>\n"
            "      </intent-filter>\n"
            "    </activity>\n"
            "  </application>\n"
            "</manifest>\n",
            encoding="utf-8",
        )
        return GeneratedProject(target, package_name, activity)
