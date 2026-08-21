#!/usr/bin/env python3
"""Autonomous coding loop for NEXTRON Builder V2."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
from core.providers.catalog import build_providers
ROOT=Path(__file__).resolve().parents[1]
MAX_ITERATIONS=max(1,int(os.getenv("NEXTRON_AGENT_MAX_ITERATIONS","5")))
BRANCH=os.getenv("NEXTRON_AGENT_BRANCH","feature/nextron-builder-v2")
ALLOWED=("core/","tests/","docs/","NEXTRON_V2_AUTONOMOUS.md")

def run(cmd:list[str],timeout:int=900):
    p=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
    return p.returncode,p.stdout[-16000:]

def snapshot():
    out=[]
    for cmd,label in [(["git","status","--short"],"GIT STATUS"),(["git","diff","--","core","tests","docs","NEXTRON_V2_AUTONOMOUS.md"],"CURRENT DIFF")]:
        _,text=run(cmd); out.append(label+":\n"+text)
    for path in ["README.md","core/app_plan.py","core/ai_planner.py","core/app_builder/contracts.py","core/app_builder/pipeline.py","core/app_builder/project_generator.py","core/app_builder/toolchain/gradle_backend.py","core/nextron.py"]:
        p=ROOT/path
        if p.is_file(): out.append(f"FILE {path}:\n"+p.read_text(encoding="utf-8",errors="replace")[-12000:])
    return "\n\n".join(out)[-50000:]

def get_provider():
    ps=build_providers(); return ps.get("openrouter") or ps.get("groq")

def ask(provider,context,iteration):
    prompt=f'''You are the senior autonomous engineer finishing NEXTRON X-100 Builder V2.
Branch: {BRANCH}. Iteration {iteration}/{MAX_ITERATIONS}.
Goal: finish the real end-to-end Android app builder, not merely tests. It must turn a natural-language request into a valid Kotlin + Jetpack Compose Android project and APK.
Rules: Kotlin + Compose only for Android UI; no Java; no XML layouts; preserve working behavior; one coherent increment; never touch secrets or CI workflow files; never delete files; changes only under core/, tests/, docs/, or NEXTRON_V2_AUTONOMOUS.md.
Return ONLY JSON: {{"summary":"...","changes":[{{"path":"relative/path","content":"complete UTF-8 file"}}],"done":false}}
If no safe useful change is justified, return changes=[] and explain.

REPOSITORY SNAPSHOT:
{context}'''
    r=provider.generate(prompt)
    if not r.success: raise RuntimeError(r.error or "AI generation failed")
    text=r.text.strip(); a=text.find("{"); b=text.rfind("}")
    if a<0 or b<=a: raise ValueError("AI did not return JSON")
    data=json.loads(text[a:b+1])
    if not isinstance(data,dict) or not isinstance(data.get("changes",[]),list): raise ValueError("Invalid AI change format")
    return data

def apply(data):
    n=0
    for c in data.get("changes",[]):
        path=str(c.get("path","")); content=c.get("content")
        if not path or content is None or path.startswith("/") or ".." in Path(path).parts: raise ValueError(f"Unsafe path: {path}")
        if not any(path==x or path.startswith(x) for x in ALLOWED): raise ValueError(f"Out-of-scope path: {path}")
        p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(str(content),encoding="utf-8"); print("APPLIED:",path); n+=1
    return n

def validate():
    logs=[]
    for cmd in [["python","-m","py_compile","core/nextron.py","core/app_plan.py","core/ai_planner.py"],["python","-m","pytest","-q"]]:
        code,text=run(cmd,1200); logs.append("$ "+" ".join(cmd)+"\n"+text)
        if code: return False,"\n\n".join(logs)
    return True,"\n\n".join(logs)

def main():
    p=get_provider()
    if p is None: print("ERROR: no AI provider configured"); return 2
    print("NEXTRON autonomous agent:",getattr(p,"model","configured provider"))
    for i in range(1,MAX_ITERATIONS+1):
        print(f"\n===== ITERATION {i}/{MAX_ITERATIONS} =====")
        try:
            data=ask(p,snapshot(),i); print("PLAN:",data.get("summary",""))
            if apply(data)==0: print("No changes proposed; stopping."); break
            ok,out=validate(); print(out)
            if not ok: print("VALIDATION FAILED; next iteration will repair.")
            else:
                print("VALIDATION PASSED")
                if data.get("done") is True: print("V2 milestone reported complete."); break
        except Exception as e: print("AGENT ERROR:",e); return 1
    print("AUTONOMOUS RUN COMPLETE"); return 0
if __name__=="__main__": raise SystemExit(main())
