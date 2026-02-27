"""SuperNova TUI — Main Application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import Hit, Hits, Provider
from textual.containers import Container
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)
from textual import work

from tui.client import SuperNovaClient


class SuperNovaCommands(Provider):
    """Command palette provider for SuperNova."""

    async def search(self, query: str) -> Hits:
        app = self.app
        commands: list[tuple[str, str, str]] = [
            ("Switch to Chat", "Open the chat tab", "tab('chat')"),
            ("Switch to Memory", "Open the memory browser", "tab('memory')"),
            ("Switch to Approvals", "Open the approval queue", "tab('approvals')"),
            ("Switch to Admin", "Open the admin dashboard", "tab('admin')"),
            ("Switch to Logs", "Open the log viewer", "tab('logs')"),
            ("Health Check", "Run a deep health check", "admin_health"),
            ("View Costs", "Show cost summary", "admin_costs"),
            ("View Audit Logs", "Show audit trail", "admin_audit"),
            ("Refresh Approvals", "Reload pending approvals", "refresh_approvals"),
            ("Search Memories", "Search semantic memories", "search_memories"),
            ("Load Skills", "View procedural skills", "load_skills"),
            ("Export Memories", "Export memories to JSON", "export_memories"),
        ]
        for name, help_text, action in commands:
            if query.lower() in name.lower():
                yield Hit(1.0, name, help=help_text, command=lambda a=action: app.run_command(a))


class SuperNovaApp(App):
    """SuperNova Terminal User Interface."""

    TITLE = "✦ SuperNova"
    SUB_TITLE = "AI Agent"
    CSS_PATH = Path("styles/app.tcss")
    COMMANDS = {SuperNovaCommands}

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+1", "tab('chat')", "Chat", show=True),
        Binding("ctrl+2", "tab('memory')", "Memory", show=True),
        Binding("ctrl+3", "tab('approvals')", "Approvals", show=True),
        Binding("ctrl+4", "tab('admin')", "Admin", show=True),
        Binding("ctrl+5", "tab('logs')", "Logs", show=True),
        Binding("ctrl+p", "command_palette", "palette", show=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.client = SuperNovaClient()
        self.connected = False
        self._approvals: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main-tabs"):
            with TabPane("💬 Chat", id="chat"):
                yield RichLog(id="chat-log", highlight=True, markup=True, wrap=True)
                with Container(id="chat-input-area"):
                    yield Input(
                        placeholder="Send a message to SuperNova…",
                        id="chat-input",
                    )
                    yield Button("Send", id="send-btn", variant="warning")
            with TabPane("🧠 Memory", id="memory"):
                yield Input(placeholder="Search semantic memories…", id="memory-search")
                yield DataTable(id="memory-table", cursor_type="row")
                with Container(id="memory-actions"):
                    yield Button("🔍 Search", id="memory-search-btn", variant="warning")
                    yield Button("📤 Export", id="memory-export-btn", variant="default")
                    yield Button("📥 Import", id="memory-import-btn", variant="default")
                    yield Button("🛠 Skills", id="memory-skills-btn", variant="default")
            with TabPane("🛡️ Approvals", id="approvals"):
                yield DataTable(id="approval-table", cursor_type="row")
                with Container(id="approval-actions"):
                    yield Button("✓ Approve", id="approve-btn", variant="success")
                    yield Button("✗ Deny", id="deny-btn", variant="error")
                    yield Button("↻ Refresh", id="refresh-approvals-btn", variant="default")
            with TabPane("📊 Admin", id="admin"):
                yield RichLog(id="admin-log", highlight=True, markup=True, wrap=True)
                with Container(id="admin-actions"):
                    yield Button("❤ Health", id="admin-health-btn", variant="success")
                    yield Button("💰 Costs", id="admin-costs-btn", variant="warning")
                    yield Button("📜 Audit", id="admin-audit-btn", variant="default")
                    yield Button("🚀 Fleet", id="admin-fleet-btn", variant="default")
            with TabPane("📋 Logs", id="logs"):
                yield RichLog(id="log-viewer", highlight=True, markup=True, wrap=True)
        yield Static(
            " ● Disconnected  │  Model: —  │  Cost: $0.00 ",
            id="status-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        chat = self.query_one("#chat-log", RichLog)
        chat.write("[bold #FFB800]✦ SuperNova[/] ready. Type a message below.\n")
        self._log("TUI started")
        self.check_connection()
        # Set up approval table columns
        table = self.query_one("#approval-table", DataTable)
        table.add_columns("Risk", "Tool", "Agent", "Expires", "ID")
        # Set up memory table columns
        mem_table = self.query_one("#memory-table", DataTable)
        mem_table.add_columns("Type", "Content", "Category")

    def _log(self, msg: str) -> None:
        try:
            viewer = self.query_one("#log-viewer", RichLog)
            viewer.write(f"[dim]{msg}[/]")
        except Exception:
            pass

    def _update_status(self, connected: bool, model: str = "—", cost: str = "$0.00") -> None:
        self.connected = connected
        dot = "[green]●[/] Connected" if connected else "[red]●[/] Disconnected"
        bar = self.query_one("#status-bar", Static)
        bar.update(f" {dot}  │  Model: {model}  │  Cost: {cost}  │  Session: {self.client.session_id[:8]} ")

    @work(exclusive=True, group="health")
    async def check_connection(self) -> None:
        try:
            data = await self.client.health()
            status = data.get("status", "unknown")
            self._update_status(status == "ok")
            self._log(f"Health check: {status}")
        except Exception as e:
            self._update_status(False)
            self._log(f"Connection failed: {e}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input" and event.value.strip():
            self.send_chat_message(event.value.strip())
            event.input.value = ""
        elif event.input.id == "memory-search":
            self.search_memories(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            inp = self.query_one("#chat-input", Input)
            if inp.value.strip():
                self.send_chat_message(inp.value.strip())
                inp.value = ""
        elif event.button.id == "approve-btn":
            self._resolve_selected(True)
        elif event.button.id == "deny-btn":
            self._resolve_selected(False)
        elif event.button.id == "refresh-approvals-btn":
            self.refresh_approvals()
        elif event.button.id == "memory-search-btn":
            query = self.query_one("#memory-search", Input).value
            self.search_memories(query)
        elif event.button.id == "memory-skills-btn":
            self.load_skills()
        elif event.button.id == "memory-export-btn":
            self.export_memories()
        elif event.button.id == "memory-import-btn":
            self.notify("Import: place JSON file in workspace/ and use API", severity="information", timeout=5)
        elif event.button.id == "admin-health-btn":
            self.load_admin_health()
        elif event.button.id == "admin-costs-btn":
            self.load_admin_costs()
        elif event.button.id == "admin-audit-btn":
            self.load_admin_audit()
        elif event.button.id == "admin-fleet-btn":
            self.load_admin_fleet()

    @work(exclusive=True, group="chat")
    async def send_chat_message(self, message: str) -> None:
        chat = self.query_one("#chat-log", RichLog)
        chat.write(f"\n[bold cyan]You:[/] {message}")
        self._log(f"Sending: {message[:80]}")

        try:
            chat.write("[dim]⏳ Streaming…[/]")
            async for event in self.client.stream(message):
                etype = event.get("type", "")
                if etype == "token":
                    # Streaming token — append to current line
                    chat.write(event.get("content", ""), shrink=False)
                elif etype == "message":
                    chat.write(f"[bold #FFB800]✦ Agent:[/] {event.get('content', '')}")
                elif etype == "tool_call":
                    name = event.get("name", "unknown")
                    chat.write(f"[dim]🔧 Calling tool: {name}[/]")
                elif etype == "tool_result":
                    chat.write(f"[dim]✓ Tool result received[/]")
                elif etype == "approval_required":
                    chat.write(f"[bold yellow]⚠ Approval needed:[/] {event.get('tool', '')}")
                    self.notify("Approval required!", severity="warning", timeout=10)
                elif etype == "error":
                    chat.write(f"[bold red]Error:[/] {event.get('message', '')}")
                elif etype == "done":
                    self._log("Stream complete")
                else:
                    # Unknown event — log it
                    self._log(f"Event: {etype} {event}")
        except Exception as e:
            chat.write(f"[bold red]Error:[/] {e}")
            self._log(f"Stream failed: {e}")
            self.notify(f"Send failed: {e}", severity="error", timeout=5)

    def action_tab(self, tab_id: str) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = tab_id
        if tab_id == "approvals":
            self.refresh_approvals()
        elif tab_id == "memory":
            self.search_memories("")
        elif tab_id == "admin":
            self.load_admin_health()

    @work(exclusive=True, group="admin")
    async def load_admin_health(self) -> None:
        log = self.query_one("#admin-log", RichLog)
        log.clear()
        log.write("[bold #FFB800]❤ Deep Health Check[/]\n")
        try:
            data = await self.client.deep_health()
            for key, val in data.items():
                if isinstance(val, dict):
                    status = val.get("status", "unknown")
                    icon = "🟢" if status == "ok" else "🔴"
                    log.write(f"  {icon} [bold]{key}[/]: {status}")
                    for k, v in val.items():
                        if k != "status":
                            log.write(f"      {k}: {v}")
                else:
                    log.write(f"  {key}: {val}")
            self._update_status(True)
        except Exception as e:
            log.write(f"[bold red]Failed:[/] {e}")
            self._update_status(False)

    @work(exclusive=True, group="admin")
    async def load_admin_costs(self) -> None:
        log = self.query_one("#admin-log", RichLog)
        log.clear()
        log.write("[bold #FFB800]💰 Cost Summary[/]\n")
        try:
            data = await self.client.get_costs()
            if isinstance(data, dict):
                for key, val in data.items():
                    log.write(f"  [bold]{key}[/]: {val}")
            elif isinstance(data, list):
                for item in data[:20]:
                    log.write(f"  {item}")
            else:
                log.write(f"  {data}")
        except Exception as e:
            log.write(f"[bold red]Failed:[/] {e}")

    @work(exclusive=True, group="admin")
    async def load_admin_audit(self) -> None:
        log = self.query_one("#admin-log", RichLog)
        log.clear()
        log.write("[bold #FFB800]📜 Audit Logs[/]\n")
        try:
            data = await self.client.get_audit_logs()
            entries = data if isinstance(data, list) else data.get("entries", data.get("logs", []))
            if isinstance(entries, list):
                for entry in entries[:30]:
                    ts = entry.get("timestamp", "")[:19] if isinstance(entry, dict) else ""
                    action = entry.get("action", "") if isinstance(entry, dict) else str(entry)
                    actor = entry.get("actor", "") if isinstance(entry, dict) else ""
                    log.write(f"  [dim]{ts}[/] {action} [dim]({actor})[/]")
            if not entries:
                log.write("  [dim]No audit entries found[/]")
        except Exception as e:
            log.write(f"[bold red]Failed:[/] {e}")

    @work(exclusive=True, group="admin")
    async def load_admin_fleet(self) -> None:
        log = self.query_one("#admin-log", RichLog)
        log.clear()
        log.write("[bold #FFB800]🚀 Fleet Status[/]\n")
        try:
            data = await self.client.get_fleet()
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, list):
                        log.write(f"  [bold]{key}[/]: {len(val)} entries")
                        for item in val[:10]:
                            log.write(f"    • {item}")
                    else:
                        log.write(f"  [bold]{key}[/]: {val}")
            else:
                log.write(f"  {data}")
        except Exception as e:
            log.write(f"[bold red]Failed:[/] {e}")

    @work(exclusive=True, group="memory")
    async def search_memories(self, query: str) -> None:
        table = self.query_one("#memory-table", DataTable)
        table.clear()
        try:
            memories = await self.client.get_semantic_memories()
            if isinstance(memories, list):
                for m in memories:
                    content = str(m.get("content", m.get("fact", "")))[:80]
                    category = str(m.get("category", ""))
                    table.add_row("🧠 Semantic", content, category)
            self._log(f"Loaded {len(memories) if isinstance(memories, list) else 0} semantic memories")
        except Exception as e:
            self._log(f"Memory search failed: {e}")
            self.notify(f"Memory load failed: {e}", severity="error", timeout=5)

    @work(exclusive=True, group="memory")
    async def load_skills(self) -> None:
        table = self.query_one("#memory-table", DataTable)
        table.clear()
        try:
            skills = await self.client.get_procedural_skills()
            if isinstance(skills, list):
                for s in skills:
                    name = str(s.get("name", s.get("skill_name", "")))[:80]
                    status = "✅" if s.get("is_active") else "❌"
                    table.add_row(f"🛠 Skill {status}", name, str(s.get("trigger", ""))[:40])
            self._log(f"Loaded {len(skills) if isinstance(skills, list) else 0} skills")
        except Exception as e:
            self._log(f"Skills load failed: {e}")
            self.notify(f"Skills load failed: {e}", severity="error", timeout=5)

    @work(exclusive=True, group="memory")
    async def export_memories(self) -> None:
        try:
            data = await self.client._http.get("/memory/export")
            data.raise_for_status()
            path = "workspace/memory_export.json"
            import json
            with open(path, "w") as f:
                json.dump(data.json(), f, indent=2)
            self.notify(f"Exported to {path}", severity="information", timeout=5)
            self._log(f"Memories exported to {path}")
        except Exception as e:
            self.notify(f"Export failed: {e}", severity="error", timeout=5)
            self._log(f"Export failed: {e}")

    @work(exclusive=True, group="approvals")
    async def refresh_approvals(self) -> None:
        table = self.query_one("#approval-table", DataTable)
        table.clear()
        self._approvals = []
        try:
            snapshot = await self.client.get_snapshot()
            self._approvals = snapshot.get("pending_approvals", [])
            for a in self._approvals:
                risk = a.get("risk", "unknown")
                risk_display = {
                    "low": "🟢 Low", "medium": "🟡 Medium",
                    "high": "🟠 High", "critical": "🔴 Critical",
                }.get(risk, f"⚪ {risk}")
                expires = a.get("expires_seconds")
                exp_str = f"{expires}s" if expires is not None else "—"
                table.add_row(risk_display, a.get("tool", ""), a.get("agent", ""), exp_str, a.get("id", "")[:8])
            self._log(f"Loaded {len(self._approvals)} pending approvals")
            if not self._approvals:
                self.notify("No pending approvals", severity="information", timeout=3)
        except Exception as e:
            self._log(f"Approval refresh failed: {e}")
            self.notify(f"Could not load approvals: {e}", severity="error", timeout=5)

    def _resolve_selected(self, approved: bool) -> None:
        table = self.query_one("#approval-table", DataTable)
        if not self._approvals:
            self.notify("No approvals to resolve", severity="warning", timeout=3)
            return
        try:
            row_idx = table.cursor_row
            approval = self._approvals[row_idx]
            self._do_resolve(approval["id"], approved)
        except Exception:
            self.notify("Select an approval first", severity="warning", timeout=3)

    @work(exclusive=True, group="resolve")
    async def _do_resolve(self, approval_id: str, approved: bool) -> None:
        action = "Approved" if approved else "Denied"
        try:
            await self.client.resolve_approval(approval_id, approved)
            self.notify(f"{action}: {approval_id[:8]}", severity="information", timeout=5)
            self._log(f"{action} approval {approval_id}")
            self.refresh_approvals()
        except Exception as e:
            self.notify(f"Resolve failed: {e}", severity="error", timeout=5)
            self._log(f"Resolve failed: {e}")

    def run_command(self, action: str) -> None:
        """Dispatch command palette actions."""
        if action.startswith("tab("):
            tab_id = action.split("'")[1]
            self.action_tab(tab_id)
        elif action == "admin_health":
            self.action_tab("admin")
            self.load_admin_health()
        elif action == "admin_costs":
            self.action_tab("admin")
            self.load_admin_costs()
        elif action == "admin_audit":
            self.action_tab("admin")
            self.load_admin_audit()
        elif action == "refresh_approvals":
            self.action_tab("approvals")
            self.refresh_approvals()
        elif action == "search_memories":
            self.action_tab("memory")
            self.search_memories("")
        elif action == "load_skills":
            self.action_tab("memory")
            self.load_skills()
        elif action == "export_memories":
            self.export_memories()

    async def action_quit(self) -> None:
        await self.client.close()
        self.exit()


def main() -> None:
    app = SuperNovaApp()
    app.run()


if __name__ == "__main__":
    main()
