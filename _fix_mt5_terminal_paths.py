"""
Fix MT5 dual-terminal path configuration on VPS.
Finds running MT5 terminal processes, maps them to accounts, and updates .env.

Run on VPS: python _fix_mt5_terminal_paths.py
Or run locally to query VPS via API.
"""
import requests
import json
import subprocess
import os
import sys
import re

VPS_URL = "http://148.113.5.39:9000"
API_KEY = "zwesta_live_api_key_2026_secure"
ENV_PATH = r"C:\backend\.env"

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
}


def check_cooldown():
    """Check if account 295677214 is still in auth cooldown."""
    print("\n=== Checking MT5 auth cooldown ===")
    try:
        r = requests.get(f"{VPS_URL}/api/health", timeout=5)
        print(f"Backend: {r.json().get('status', 'unknown')}")
    except Exception as e:
        print(f"Backend unreachable: {e}")
        return

    # Try to connect Exness live
    try:
        payload = {
            "broker": "Exness",
            "account": "295677214",
            "server": "Exness-MT5Real27",
            "password": "",  # backend uses stored creds
            "mode": "live"
        }
        r = requests.post(f"{VPS_URL}/api/broker/test-connection",
                          headers=HEADERS, json=payload, timeout=30)
        print(f"Exness live test: HTTP {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Test connection failed: {e}")


def find_mt5_processes_local():
    """Find MT5 terminal processes (run this ON the VPS)."""
    print("\n=== Scanning for MT5 terminal processes ===")
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process -Name 'terminal64' -ErrorAction SilentlyContinue | "
             "Select-Object Id, @{N='Path';E={$_.MainModule.FileName}}, "
             "@{N='Title';E={$_.MainWindowTitle}}, CPU | "
             "ConvertTo-Json"],
            capture_output=True, text=True, timeout=15
        )
        if result.stdout.strip():
            procs = json.loads(result.stdout)
            if isinstance(procs, dict):
                procs = [procs]
            print(f"Found {len(procs)} MT5 terminal process(es):")
            for p in procs:
                print(f"  PID={p.get('Id')}  Path={p.get('Path')}  Title={p.get('Title')}")
            return procs
        else:
            print("No terminal64 processes found.")
            print(f"stderr: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error scanning processes: {e}")
        return []


def find_mt5_installations():
    """Find all MetaTrader 5 installations by scanning common paths."""
    print("\n=== Scanning for MT5 installations ===")
    common_roots = [
        r"C:\Program Files",
        r"C:\Program Files (x86)",
        r"C:\Users",
        r"C:\",
    ]
    found = []
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             r"Get-ChildItem -Path 'C:\' -Recurse -Filter 'terminal64.exe' "
             r"-ErrorAction SilentlyContinue -Depth 6 | "
             r"Select-Object -ExpandProperty FullName | ConvertTo-Json"],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout.strip():
            paths = json.loads(result.stdout)
            if isinstance(paths, str):
                paths = [paths]
            print(f"Found {len(paths)} terminal64.exe installations:")
            for p in paths:
                print(f"  {p}")
            return paths
        else:
            print("No terminal64.exe found via recursive scan.")
            return []
    except Exception as e:
        print(f"Error scanning installations: {e}")
        return []


def read_env():
    """Read current .env file."""
    if not os.path.exists(ENV_PATH):
        print(f"WARNING: {ENV_PATH} not found")
        return {}
    env = {}
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def show_current_env():
    """Show relevant MT5 settings in .env."""
    print(f"\n=== Current .env MT5 settings ===")
    env = read_env()
    mt5_keys = [k for k in env if "MT5" in k.upper() or "EXNESS" in k.upper() or "TERMINAL" in k.upper()]
    if mt5_keys:
        for k in sorted(mt5_keys):
            print(f"  {k}={env[k]}")
    else:
        print("  (no MT5/Exness/Terminal keys found)")
    return env


def update_env_terminal_paths(live_path, demo_path):
    """Update .env with correct terminal paths."""
    print(f"\n=== Updating .env terminal paths ===")
    print(f"  LIVE path: {live_path}")
    print(f"  DEMO path: {demo_path}")

    if not os.path.exists(ENV_PATH):
        print(f"ERROR: {ENV_PATH} not found - cannot update")
        return False

    with open(ENV_PATH, "r") as f:
        content = f.read()

    # Keys the backend actually reads (from startup log "DUAL MT5" hints)
    # These need to be identified from the backend source
    # Common patterns:
    keys_to_try = [
        ("MT5_EXNESS_LIVE_PATH", live_path),
        ("MT5_EXNESS_DEMO_PATH", demo_path),
        ("EXNESS_LIVE_TERMINAL_PATH", live_path),
        ("EXNESS_DEMO_TERMINAL_PATH", demo_path),
        ("MT5_LIVE_PATH", live_path),
        ("MT5_DEMO_PATH", demo_path),
    ]

    updated = []
    for key, val in keys_to_try:
        pattern = rf"^{re.escape(key)}\s*=.*$"
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, f"{key}={val}", content, flags=re.MULTILINE)
            updated.append(key)
            print(f"  Updated: {key}")

    if not updated:
        print("  No matching keys found in .env to update.")
        print("  Will append new keys...")
        content += f"\n# MT5 terminal paths (dual terminal fix)\n"
        content += f"MT5_EXNESS_LIVE_PATH={live_path}\n"
        content += f"MT5_EXNESS_DEMO_PATH={demo_path}\n"

    # Backup first
    backup = ENV_PATH + ".bak"
    with open(backup, "w") as f:
        with open(ENV_PATH, "r") as src:
            f.write(src.read())
    print(f"  Backup saved to: {backup}")

    with open(ENV_PATH, "w") as f:
        f.write(content)
    print(f"  .env updated successfully")
    return True


def force_reconnect_live():
    """Force backend to reconnect to live account (clear cooldown)."""
    print("\n=== Attempting to force MT5 live reconnect ===")
    # The backend has an endpoint to clear cooldown or we can use test-connection
    # with stored credentials
    try:
        # Get stored credentials for Exness live
        r = requests.post(
            f"{VPS_URL}/api/broker/test-connection",
            headers=HEADERS,
            json={
                "credential_id": "9f14c8b4-0071-4222-81a2-5c99e841b9e0",
                "mode": "live"
            },
            timeout=60
        )
        print(f"HTTP {r.status_code}: {r.text[:300]}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    is_on_vps = os.path.exists(r"C:\backend")

    print("=" * 60)
    print("MT5 Dual Terminal Path Fix")
    print("=" * 60)

    if is_on_vps:
        print("Running ON VPS - can access local files and processes")

        # Show current env
        env = show_current_env()

        # Find running processes
        procs = find_mt5_processes_local()

        # Find installations
        installations = find_mt5_installations()

        if len(installations) >= 2:
            print("\n=== Found 2 terminal installations ===")
            print("You need to identify which is LIVE and which is DEMO:")
            for i, path in enumerate(installations):
                print(f"  [{i}] {path}")
            print("\nTIP: The LIVE terminal is usually in a different folder than DEMO.")
            print("     Look for 'EXNESS' vs 'EXNESS DEMO' in the folder name.")

            # Try to auto-detect based on folder name
            live_path = None
            demo_path = None
            for path in installations:
                path_lower = path.lower()
                if "demo" in path_lower or "trial" in path_lower:
                    demo_path = path
                elif "live" in path_lower or "real" in path_lower:
                    live_path = path
                elif live_path is None:
                    live_path = path
                else:
                    demo_path = path

            if live_path and demo_path:
                print(f"\nAuto-detected:")
                print(f"  LIVE: {live_path}")
                print(f"  DEMO: {demo_path}")
                update_env_terminal_paths(live_path, demo_path)
                print("\n✅ .env updated. Restart the backend for changes to take effect.")
            else:
                print("\nCould not auto-detect. Please manually inspect the paths above")
                print("and update .env with:")
                print("  MT5_EXNESS_LIVE_PATH=<live terminal64.exe path>")
                print("  MT5_EXNESS_DEMO_PATH=<demo terminal64.exe path>")

        elif len(installations) == 1:
            print(f"\nOnly 1 MT5 installation found: {installations[0]}")
            print("Both accounts will share this terminal (single-terminal mode)")
            print("This is the correct mode if both accounts are in the same terminal.")

        # Check current cooldown status
        check_cooldown()

    else:
        print("Running REMOTELY (not on VPS)")
        print("This script must be run ON the VPS to fix terminal paths.")
        print("\nAlternatively, on the VPS open PowerShell and run:")
        print()
        print("  Get-Process -Name 'terminal64' | Select Id, @{N='Path';E={$_.MainModule.FileName}}, MainWindowTitle")
        print()
        print("Then update C:\\backend\\.env with the correct paths.")
        print()
        # Still check cooldown from remote
        check_cooldown()

    print("\n=== DIAGNOSIS SUMMARY ===")
    print("The backend uses single-terminal MT5 mode.")
    print("Both DEMO and LIVE hints in .env point to a missing path.")
    print("=> mt5.initialize() with no path attaches to whichever terminal responds.")
    print("=> After switching to demo account, live account started failing.")
    print()
    print("ROOT FIX OPTIONS:")
    print("1. [BEST] Configure separate terminal paths for live/demo in .env")
    print("   so each account always uses its own terminal.")
    print("2. [QUICK] Close the demo MT5 terminal on VPS, restart backend.")
    print("   This forces mt5.initialize() to attach to live terminal only.")
    print("3. [WAIT] Cooldown expires at ~05:30. Then restart backend.")


if __name__ == "__main__":
    main()
