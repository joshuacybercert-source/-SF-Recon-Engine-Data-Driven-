import json
import os
import platform
import re
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from tkinter import Button, END, Frame, Label, Scrollbar, Text, Tk, filedialog, messagebox


@dataclass
class CheckResult:
    check_id: str
    title: str
    status: str  # PASS, WARN, FAIL, INFO
    details: str
    remediation: str = ""


def run_command(cmd, timeout=10):
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = (completed.stdout or "").strip()
        if not output:
            output = (completed.stderr or "").strip()
        return output
    except (subprocess.SubprocessError, OSError):
        return ""


def is_windows():
    return platform.system().lower() == "windows"


def is_macos():
    return platform.system().lower() == "darwin"


def is_linux():
    return platform.system().lower() == "linux"


def command_exists(command):
    return shutil.which(command) is not None


def parse_iso_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def check_os():
    info = f"{platform.system()} {platform.release()} ({platform.version()})"
    return CheckResult(
        check_id="os",
        title="Operating system",
        status="INFO",
        details=f"Detected OS: {info}. Python: {platform.python_version()}",
    )


def parse_netsh_interfaces(output):
    data = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        left, right = line.split(":", 1)
        key = left.strip().lower()
        value = right.strip()
        if key:
            data[key] = value
    return data


def check_wifi():
    results = []
    if is_macos():
        output = run_command(["networksetup", "-getairportnetwork", "en0"])
        ssid = "unknown"
        if "Current Wi-Fi Network" in output:
            ssid = output.split(":")[-1].strip()
        airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
        signal_output = ""
        if os.path.exists(airport_path):
            signal_output = run_command([airport_path, "-I"])
        rssi = "unknown"
        for line in signal_output.splitlines():
            if "agrCtlRSSI" in line:
                rssi = line.split(":")[-1].strip()
        results.append(
            CheckResult(
                check_id="wifi-connection",
                title="Wi-Fi connection",
                status="INFO",
                details=f"SSID: {ssid}. RSSI: {rssi}.",
            )
        )
        return results

    if is_linux():
        if command_exists("nmcli"):
            output = run_command(
                ["nmcli", "-t", "-f", "ACTIVE,SSID,SECURITY,SIGNAL", "dev", "wifi"]
            )
            active = [line for line in output.splitlines() if line.startswith("yes:")]
            if active:
                parts = active[0].split(":")
                ssid = parts[1] if len(parts) > 1 else "unknown"
                security = parts[2] if len(parts) > 2 else "unknown"
                signal = parts[3] if len(parts) > 3 else "unknown"
                status = "PASS" if security and security != "--" else "WARN"
                remediation = "" if status == "PASS" else "Use WPA2 or WPA3 on your router."
                results.append(
                    CheckResult(
                        check_id="wifi-security",
                        title="Wi-Fi encryption",
                        status=status,
                        details=f"SSID: {ssid}. Security: {security}. Signal: {signal}%.",
                        remediation=remediation,
                    )
                )
                return results
        results.append(
            CheckResult(
                check_id="wifi",
                title="Wi-Fi security",
                status="INFO",
                details="No supported Wi-Fi command found.",
            )
        )
        return results

    if not is_windows():
        results.append(
            CheckResult(
                check_id="wifi",
                title="Wi-Fi security",
                status="INFO",
                details="Wi-Fi checks are only supported on Windows/macOS/Linux.",
            )
        )
        return results

    output = run_command(["netsh", "wlan", "show", "interfaces"])
    if not output:
        results.append(
            CheckResult(
                check_id="wifi",
                title="Wi-Fi security",
                status="INFO",
                details="Could not read Wi-Fi interface details.",
            )
        )
        return results

    info = parse_netsh_interfaces(output)
    state = info.get("state", "unknown")
    ssid = info.get("ssid", "unknown")
    auth = info.get("authentication", "unknown")
    cipher = info.get("cipher", "unknown")
    signal = info.get("signal", "unknown")
    radio = info.get("radio type", "unknown")

    if state.lower() != "connected":
        results.append(
            CheckResult(
                check_id="wifi-connection",
                title="Wi-Fi connection",
                status="WARN",
                details=f"Not connected (state: {state}).",
                remediation="Connect to a trusted network to run Wi-Fi checks.",
            )
        )
        return results

    auth_lower = auth.lower()
    if "wpa3" in auth_lower or "wpa2" in auth_lower:
        status = "PASS"
        remediation = ""
    elif "wep" in auth_lower or "open" in auth_lower:
        status = "FAIL"
        remediation = "Use WPA2 or WPA3 on your router and reconnect."
    else:
        status = "WARN"
        remediation = "Verify your router security settings."

    details = (
        f"SSID: {ssid}. Auth: {auth}. Cipher: {cipher}. "
        f"Signal: {signal}. Radio: {radio}."
    )
    results.append(
        CheckResult(
            check_id="wifi-security",
            title="Wi-Fi encryption",
            status=status,
            details=details,
            remediation=remediation,
        )
    )

    signal_match = re.search(r"(\d+)%", signal)
    if signal_match:
        signal_pct = int(signal_match.group(1))
        if signal_pct >= 70:
            status = "PASS"
            remediation = ""
        elif signal_pct >= 40:
            status = "WARN"
            remediation = "Move closer to the router or reduce interference."
        else:
            status = "FAIL"
            remediation = "Signal is weak; improve placement or use Ethernet."
        results.append(
            CheckResult(
                check_id="wifi-signal",
                title="Wi-Fi signal strength",
                status=status,
                details=f"Signal strength: {signal_pct}%.",
                remediation=remediation,
            )
        )

    return results


def check_firewall():
    if is_windows():
        output = run_command(["netsh", "advfirewall", "show", "allprofiles"])
        if not output:
            return CheckResult(
                check_id="firewall",
                title="Firewall",
                status="INFO",
                details="Could not read firewall status.",
            )

        states = []
        for line in output.splitlines():
            line = line.strip()
            if line.lower().startswith("state"):
                parts = line.split()
                if parts:
                    states.append(parts[-1].upper())

        if states and all(state == "ON" for state in states):
            return CheckResult(
                check_id="firewall",
                title="Firewall",
                status="PASS",
                details="Firewall is ON for all profiles.",
            )
        return CheckResult(
            check_id="firewall",
            title="Firewall",
            status="WARN",
            details="One or more firewall profiles are OFF.",
            remediation="Enable Windows Firewall for all profiles.",
        )

    if is_macos():
        output = run_command(
            ["defaults", "read", "/Library/Preferences/com.apple.alf", "globalstate"]
        )
        state = output.strip()
        if state == "1" or state == "2":
            return CheckResult(
                check_id="firewall",
                title="Firewall",
                status="PASS",
                details="macOS Application Firewall appears enabled.",
            )
        return CheckResult(
            check_id="firewall",
            title="Firewall",
            status="WARN",
            details="macOS Application Firewall appears disabled.",
            remediation="Enable the Application Firewall in System Settings.",
        )

    if is_linux():
        if command_exists("ufw"):
            output = run_command(["ufw", "status"])
            if "Status: active" in output:
                return CheckResult(
                    check_id="firewall",
                    title="Firewall",
                    status="PASS",
                    details="UFW firewall is active.",
                )
            return CheckResult(
                check_id="firewall",
                title="Firewall",
                status="WARN",
                details="UFW firewall is inactive.",
                remediation="Enable UFW or your preferred firewall.",
            )

        if command_exists("firewall-cmd"):
            output = run_command(["firewall-cmd", "--state"])
            if output.strip().lower() == "running":
                return CheckResult(
                    check_id="firewall",
                    title="Firewall",
                    status="PASS",
                    details="firewalld is running.",
                )
            return CheckResult(
                check_id="firewall",
                title="Firewall",
                status="WARN",
                details="firewalld is not running.",
                remediation="Enable firewalld or your preferred firewall.",
            )

        return CheckResult(
            check_id="firewall",
            title="Firewall",
            status="INFO",
            details="No supported firewall command found.",
        )

    return CheckResult(
        check_id="firewall",
        title="Firewall",
        status="INFO",
        details="Firewall check not supported on this OS.",
    )


def check_defender():
    if not is_windows():
        return CheckResult(
            check_id="defender",
            title="Defender real-time protection",
            status="INFO",
            details="Defender check is only supported on Windows.",
        )

    output = run_command(
        [
            "powershell",
            "-Command",
            "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled",
        ]
    )
    if not output:
        return CheckResult(
            check_id="defender",
            title="Defender real-time protection",
            status="INFO",
            details="Could not read Defender status.",
        )

    enabled = output.strip().lower() == "true"
    if enabled:
        return CheckResult(
            check_id="defender",
            title="Defender real-time protection",
            status="PASS",
            details="Defender real-time protection is enabled.",
        )
    return CheckResult(
        check_id="defender",
        title="Defender real-time protection",
        status="WARN",
        details="Defender real-time protection is disabled.",
        remediation="Enable real-time protection in Windows Security.",
    )


def check_disk_encryption():
    if is_windows():
        output = run_command(["manage-bde", "-status"])
        if not output:
            return CheckResult(
                check_id="disk-encryption",
                title="Disk encryption",
                status="INFO",
                details="Could not read BitLocker status.",
            )

        protection_on = "Protection Status: Protection On" in output
        fully_encrypted = "Conversion Status: Fully Encrypted" in output
        if protection_on or fully_encrypted:
            return CheckResult(
                check_id="disk-encryption",
                title="Disk encryption",
                status="PASS",
                details="BitLocker protection appears enabled.",
            )

        return CheckResult(
            check_id="disk-encryption",
            title="Disk encryption",
            status="WARN",
            details="BitLocker protection does not appear enabled.",
            remediation="Enable BitLocker if your device supports it.",
        )

    if is_macos():
        output = run_command(["fdesetup", "status"])
        if "FileVault is On" in output:
            return CheckResult(
                check_id="disk-encryption",
                title="Disk encryption",
                status="PASS",
                details="FileVault is enabled.",
            )
        return CheckResult(
            check_id="disk-encryption",
            title="Disk encryption",
            status="WARN",
            details="FileVault appears disabled.",
            remediation="Enable FileVault in System Settings.",
        )

    if is_linux():
        if os.path.exists("/dev/mapper"):
            return CheckResult(
                check_id="disk-encryption",
                title="Disk encryption",
                status="INFO",
                details="Check disk encryption manually for your distribution.",
            )
        return CheckResult(
            check_id="disk-encryption",
            title="Disk encryption",
            status="INFO",
            details="Disk encryption status not detected.",
        )

    return CheckResult(
        check_id="disk-encryption",
        title="Disk encryption",
        status="INFO",
        details="Disk encryption check not supported on this OS.",
    )


def check_os_updates():
    if is_windows():
        output = run_command(
            [
                "powershell",
                "-Command",
                "(Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1).InstalledOn.ToString('yyyy-MM-dd')",
            ]
        )
        last_date = parse_iso_date(output)
        if not last_date:
            return CheckResult(
                check_id="updates",
                title="OS updates",
                status="INFO",
                details="Could not determine last update date.",
            )
        delta_days = (datetime.now() - last_date).days
        if delta_days <= 30:
            status = "PASS"
            remediation = ""
        elif delta_days <= 90:
            status = "WARN"
            remediation = "Check Windows Update for pending updates."
        else:
            status = "FAIL"
            remediation = "Install updates as soon as possible."
        return CheckResult(
            check_id="updates",
            title="OS updates",
            status=status,
            details=f"Last update installed {delta_days} days ago.",
            remediation=remediation,
        )

    if is_macos():
        return CheckResult(
            check_id="updates",
            title="OS updates",
            status="INFO",
            details="Run System Settings to confirm macOS updates.",
        )

    if is_linux():
        return CheckResult(
            check_id="updates",
            title="OS updates",
            status="INFO",
            details="Run your package manager to check for updates.",
        )

    return CheckResult(
        check_id="updates",
        title="OS updates",
        status="INFO",
        details="Update checks not supported on this OS.",
    )


def check_password_policy():
    if is_windows():
        output = run_command(["net", "accounts"])
        if not output:
            return CheckResult(
                check_id="password-policy",
                title="Password policy",
                status="INFO",
                details="Could not read password policy.",
            )
        min_length = None
        max_age = None
        for line in output.splitlines():
            if "Minimum password length" in line:
                min_length = int(re.findall(r"(\d+)", line)[0])
            if "Maximum password age" in line:
                values = re.findall(r"(\d+)", line)
                if values:
                    max_age = int(values[0])
        status = "INFO"
        remediation = ""
        details_parts = []
        if min_length is not None:
            details_parts.append(f"Min length: {min_length}")
            if min_length >= 12:
                status = "PASS"
            elif min_length >= 8:
                status = "WARN"
                remediation = "Increase minimum length to 12+ characters."
            else:
                status = "FAIL"
                remediation = "Increase minimum length to 12+ characters."
        if max_age is not None:
            details_parts.append(f"Max age: {max_age} days")
            if max_age == 0:
                status = "WARN"
                remediation = "Set a maximum password age (e.g., 90 days)."
        return CheckResult(
            check_id="password-policy",
            title="Password policy",
            status=status,
            details=", ".join(details_parts) if details_parts else "Policy not found.",
            remediation=remediation,
        )

    if is_linux():
        min_length = None
        max_age = None
        try:
            with open("/etc/login.defs", "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line.startswith("#") or not line:
                        continue
                    if line.startswith("PASS_MIN_LEN"):
                        min_length = int(line.split()[-1])
                    if line.startswith("PASS_MAX_DAYS"):
                        max_age = int(line.split()[-1])
        except OSError:
            return CheckResult(
                check_id="password-policy",
                title="Password policy",
                status="INFO",
                details="Could not read /etc/login.defs.",
            )

        status = "INFO"
        remediation = ""
        details_parts = []
        if min_length is not None:
            details_parts.append(f"Min length: {min_length}")
            if min_length >= 12:
                status = "PASS"
            elif min_length >= 8:
                status = "WARN"
                remediation = "Increase PASS_MIN_LEN to 12+."
            else:
                status = "FAIL"
                remediation = "Increase PASS_MIN_LEN to 12+."
        if max_age is not None:
            details_parts.append(f"Max age: {max_age} days")
        return CheckResult(
            check_id="password-policy",
            title="Password policy",
            status=status,
            details=", ".join(details_parts) if details_parts else "Policy not found.",
            remediation=remediation,
        )

    return CheckResult(
        check_id="password-policy",
        title="Password policy",
        status="INFO",
        details="Password policy check not supported on this OS.",
    )


def check_admin_accounts():
    if is_windows():
        output = run_command(["net", "localgroup", "Administrators"])
        if not output:
            return CheckResult(
                check_id="admin-accounts",
                title="Admin accounts",
                status="INFO",
                details="Could not read Administrators group.",
            )
        members = []
        capture = False
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("---"):
                capture = True
                continue
            if capture:
                if line.lower().startswith("the command"):
                    break
                if line:
                    members.append(line)
        status = "PASS"
        remediation = ""
        if len(members) > 3:
            status = "WARN"
            remediation = "Review and remove unnecessary admin accounts."
        details = f"Admin members ({len(members)}): {', '.join(members) if members else 'none'}"
        return CheckResult(
            check_id="admin-accounts",
            title="Admin accounts",
            status=status,
            details=details,
            remediation=remediation,
        )

    if is_macos():
        output = run_command(["dscl", ".", "-read", "/Groups/admin", "GroupMembership"])
        members = []
        if output:
            parts = output.split("GroupMembership:")[-1].strip().split()
            members = [member.strip() for member in parts if member.strip()]
        status = "PASS" if len(members) <= 3 else "WARN"
        remediation = "Review admin group membership." if status == "WARN" else ""
        details = f"Admin members ({len(members)}): {', '.join(members) if members else 'none'}"
        return CheckResult(
            check_id="admin-accounts",
            title="Admin accounts",
            status=status,
            details=details,
            remediation=remediation,
        )

    if is_linux():
        members = []
        try:
            with open("/etc/group", "r", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("sudo:") or line.startswith("wheel:"):
                        parts = line.strip().split(":")
                        if len(parts) >= 4 and parts[3]:
                            members.extend([m.strip() for m in parts[3].split(",") if m])
        except OSError:
            return CheckResult(
                check_id="admin-accounts",
                title="Admin accounts",
                status="INFO",
                details="Could not read /etc/group.",
            )
        status = "PASS" if len(members) <= 3 else "WARN"
        remediation = "Review sudo/wheel members." if status == "WARN" else ""
        details = f"Admin members ({len(members)}): {', '.join(members) if members else 'none'}"
        return CheckResult(
            check_id="admin-accounts",
            title="Admin accounts",
            status=status,
            details=details,
            remediation=remediation,
        )

    return CheckResult(
        check_id="admin-accounts",
        title="Admin accounts",
        status="INFO",
        details="Admin check not supported on this OS.",
    )


def run_checks():
    results = [check_os()]
    results.extend(check_wifi())
    results.append(check_os_updates())
    results.append(check_password_policy())
    results.append(check_admin_accounts())
    results.append(check_firewall())
    results.append(check_defender())
    results.append(check_disk_encryption())
    return results


def summarize_results(results):
    lines = []
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "INFO": 0}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
        line = f"[{result.status}] {result.title} - {result.details}"
        if result.remediation:
            line += f" Remediation: {result.remediation}"
        lines.append((result.status, line))
    summary = (
        f"Summary: PASS={counts['PASS']}, WARN={counts['WARN']}, "
        f"FAIL={counts['FAIL']}, INFO={counts['INFO']}"
    )
    return summary, lines, counts


def build_html_report(results, counts, timestamp):
    rows = []
    for result in results:
        rows.append(
            "<tr>"
            f"<td class=\"{result.status}\">{result.status}</td>"
            f"<td>{result.title}</td>"
            f"<td>{result.details}</td>"
            f"<td>{result.remediation}</td>"
            "</tr>"
        )
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Security Posture Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f4f4f4; }}
    .PASS {{ color: #1a7f37; }}
    .WARN {{ color: #b35900; }}
    .FAIL {{ color: #b42318; }}
    .INFO {{ color: #1f5aa6; }}
  </style>
</head>
<body>
  <h2>Security Posture Report</h2>
  <p>Scan time: {timestamp}</p>
  <p>Summary: PASS={counts['PASS']}, WARN={counts['WARN']}, FAIL={counts['FAIL']}, INFO={counts['INFO']}</p>
  <table>
    <thead>
      <tr>
        <th>Status</th>
        <th>Check</th>
        <th>Details</th>
        <th>Remediation</th>
      </tr>
    </thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>"""


def build_fix_tips(results):
    tips = []
    for result in results:
        if result.status in ("WARN", "FAIL") and result.remediation:
            tips.append(f"{result.title}: {result.remediation}")

    if not tips:
        return ["No fixes needed. Your system looks good."]

    tips = list(dict.fromkeys(tips))
    if len(tips) > 8:
        tips = tips[:8] + ["Review remaining items in the full report."]
    return tips


class SecurityPostureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Security Posture + Wi-Fi Health Check")
        self.results = []
        self.last_timestamp = ""
        self.last_counts = {}

        title = Label(
            root,
            text="Security Posture + Wi-Fi Health Check",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(pady=(8, 2))

        header = Label(
            root,
            text="Local-only checks. No network scanning or offensive actions.",
        )
        header.pack(pady=(0, 8))

        button_frame = Frame(root)
        button_frame.pack(pady=4)

        run_button = Button(button_frame, text="Run Scan", command=self.run_scan)
        run_button.grid(row=0, column=0, padx=6)

        export_json_button = Button(button_frame, text="Export JSON", command=self.export_json)
        export_json_button.grid(row=0, column=1, padx=6)

        export_html_button = Button(button_frame, text="Export HTML", command=self.export_html)
        export_html_button.grid(row=0, column=2, padx=6)

        export_pdf_button = Button(button_frame, text="Export PDF", command=self.export_pdf)
        export_pdf_button.grid(row=0, column=3, padx=6)

        self.status_label = Label(root, text="Ready.")
        self.status_label.pack(pady=4)

        text_frame = Frame(root)
        text_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.text = Text(text_frame, wrap="word", height=20)
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.tag_config("PASS", foreground="#1a7f37")
        self.text.tag_config("WARN", foreground="#b35900")
        self.text.tag_config("FAIL", foreground="#b42318")
        self.text.tag_config("INFO", foreground="#1f5aa6")
        self.text.tag_config("HEADER", font=("Segoe UI", 10, "bold"))

        tips_frame = Frame(root)
        tips_frame.pack(fill="x", padx=8, pady=(0, 8))

        tips_label = Label(tips_frame, text="Fix tips (prioritized):", font=("Segoe UI", 10, "bold"))
        tips_label.pack(anchor="w")

        self.tips_text = Text(tips_frame, wrap="word", height=6)
        self.tips_text.pack(fill="x", expand=False)
        self.tips_text.configure(state="disabled")

    def run_scan(self):
        self.text.delete(1.0, END)
        self.status_label.config(text="Running scan...")
        self.root.update_idletasks()
        self.results = run_checks()
        self.last_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary, lines, counts = summarize_results(self.results)
        self.last_counts = counts
        self.text.insert(END, f"Scan time: {self.last_timestamp}\n", "HEADER")
        self.text.insert(END, summary + "\n\n", "HEADER")
        for status, line in lines:
            self.text.insert(END, line + "\n", status)
        self.status_label.config(text="Scan complete.")
        self.render_fix_tips()

    def render_fix_tips(self):
        tips = build_fix_tips(self.results)
        self.tips_text.configure(state="normal")
        self.tips_text.delete(1.0, END)
        for tip in tips:
            self.tips_text.insert(END, f"- {tip}\n")
        self.tips_text.configure(state="disabled")

    def export_json(self):
        if not self.results:
            messagebox.showinfo("Export JSON", "Run a scan first.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"security_posture_report_{timestamp}.json"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not file_path:
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "results": [result.__dict__ for result in self.results],
        }
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        messagebox.showinfo("Export JSON", f"Report saved to: {file_path}")

    def export_html(self):
        if not self.results:
            messagebox.showinfo("Export HTML", "Run a scan first.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"security_posture_report_{timestamp}.html"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not file_path:
            return
        _, _, counts = summarize_results(self.results)
        html = build_html_report(self.results, counts, self.last_timestamp or timestamp)
        with open(file_path, "w", encoding="utf-8") as handle:
            handle.write(html)
        messagebox.showinfo("Export HTML", f"Report saved to: {file_path}")

    def export_pdf(self):
        if not self.results:
            messagebox.showinfo("Export PDF", "Run a scan first.")
            return
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            messagebox.showerror(
                "Export PDF",
                "PDF export requires the reportlab package. Install with: pip install reportlab",
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"security_posture_report_{timestamp}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_name,
        )
        if not file_path:
            return

        summary, lines, counts = summarize_results(self.results)
        canvas_pdf = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        text_obj = canvas_pdf.beginText(40, height - 40)
        text_obj.textLine("Security Posture Report")
        text_obj.textLine(f"Scan time: {self.last_timestamp or timestamp}")
        text_obj.textLine(
            f"Summary: PASS={counts['PASS']}, WARN={counts['WARN']}, "
            f"FAIL={counts['FAIL']}, INFO={counts['INFO']}"
        )
        text_obj.textLine("")
        for status, line in lines:
            wrapped = textwrap.wrap(line, width=100)
            if not wrapped:
                text_obj.textLine("")
                continue
            for wrapped_line in wrapped:
                text_obj.textLine(wrapped_line)
        canvas_pdf.drawText(text_obj)
        canvas_pdf.showPage()
        canvas_pdf.save()
        messagebox.showinfo("Export PDF", f"Report saved to: {file_path}")


def main():
    root = Tk()
    app = SecurityPostureApp(root)
    root.geometry("800x500")
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
