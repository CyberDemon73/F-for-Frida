"""
CLI Interface for F-for-Frida
Enhanced command-line interface using Click and Rich
"""

import sys
import click
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from . import __version__
from .core.device import DeviceManager
from .core.frida_manager import FridaManager
from .core.adb import ADBClient
from .core.wireless import WirelessADB
from .core.scripts import ScriptManager, BUILTIN_SCRIPTS
from .core.doctor import Doctor, CheckStatus
from .core.hooker import AppHooker, HookMode
from .utils.logger import setup_logging, get_logger
from .utils.downloader import get_latest_frida_version, get_available_versions
from .utils.config import get_config, get_config_manager

# Initialize Rich console
console = Console()
logger = get_logger(__name__)


def print_banner():
    """Display application banner."""
    # ASCII art logo
    logo = """
[bold cyan]
    ███████╗   ███████╗ ██████╗ ██████╗     ███████╗██████╗ ██╗██████╗  █████╗ 
    ██╔════╝   ██╔════╝██╔═══██╗██╔══██╗    ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗
    █████╗     █████╗  ██║   ██║██████╔╝    █████╗  ██████╔╝██║██║  ██║███████║
    ██╔══╝     ██╔══╝  ██║   ██║██╔══██╗    ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║
    ██║        ██║     ╚██████╔╝██║  ██║    ██║     ██║  ██║██║██████╔╝██║  ██║
    ╚═╝        ╚═╝      ╚═════╝ ╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝
[/bold cyan]"""
    
    console.print(logo)
    
    # Info panel
    info_text = (
        f"[bold white]Automated Frida Server Management for Android[/bold white]\n"
        f"[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]\n"
        f"[cyan]Version:[/cyan] [bold green]{__version__}[/bold green]  "
        f"[cyan]Author:[/cyan] [yellow]Mohamed Hisham Sharaf[/yellow]\n"
        f"[dim]GitHub: github.com/CyberDemon73/F-for-Frida[/dim]"
    )
    
    console.print(Panel(
        info_text,
        border_style="cyan",
        padding=(0, 2),
    ))
    console.print()


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[bold cyan]→[/bold cyan] {message}")


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version information')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, version, verbose, log_file):
    """
    F-for-Frida - Automated Frida Server Management for Android
    
    Manage Frida server installation and execution on Android devices
    with support for multiple connected devices.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Setup logging
    import logging
    level = logging.DEBUG if verbose else logging.INFO
    setup_logging(level=level, log_file=log_file, console=False, verbose=verbose)
    
    if version:
        console.print(f"F-for-Frida version [bold cyan]{__version__}[/bold cyan]")
        ctx.exit(0)
    
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(ctx.get_help())


# ============================================
# Device Commands
# ============================================

@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed device information')
def devices(detailed):
    """List all connected Android devices."""
    print_info("Scanning for connected devices...")
    
    dm = DeviceManager()
    device_list = dm.get_connected_devices()
    
    if not device_list:
        print_warning("No devices connected")
        console.print("\n[dim]Tip: Connect your device via USB and enable USB debugging[/dim]")
        return
    
    table = Table(title="Connected Devices", box=box.ROUNDED)
    table.add_column("Serial", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Model", style="yellow")
    
    if detailed:
        table.add_column("Android", style="magenta")
        table.add_column("Architecture", style="blue")
        table.add_column("Rooted", style="red")
    
    for device in device_list:
        if detailed and device.is_authorized:
            info = dm.get_device_info(device.serial)
            if info:
                rooted = "[green]Yes[/green]" if info.is_rooted else "[red]No[/red]"
                table.add_row(
                    device.serial,
                    device.status,
                    info.model,
                    info.android_version,
                    info.frida_architecture,
                    rooted
                )
            else:
                table.add_row(device.serial, device.status, device.model or "N/A")
        else:
            status_color = "green" if device.is_authorized else "red"
            table.add_row(
                device.serial,
                f"[{status_color}]{device.status}[/{status_color}]",
                device.model or "N/A"
            )
    
    console.print(table)


# ============================================
# Wireless ADB Commands
# ============================================

@cli.group()
def wireless():
    """Wireless ADB connection management."""
    pass


@wireless.command("connect")
@click.argument('address')
def wireless_connect(address):
    """Connect to a device over WiFi (IP:PORT or just IP)."""
    w = WirelessADB()
    
    print_info(f"Connecting to {address}...")
    success, message = w.connect(address)
    
    if success:
        print_success(message)
    else:
        print_error(message)


@wireless.command("disconnect")
@click.argument('address', required=False)
def wireless_disconnect(address):
    """Disconnect from wireless device(s)."""
    w = WirelessADB()
    
    if address:
        print_info(f"Disconnecting from {address}...")
    else:
        print_info("Disconnecting all wireless devices...")
    
    success, message = w.disconnect(address)
    
    if success:
        print_success(message)
    else:
        print_error(message)


@wireless.command("setup")
@click.option('--device', '-s', help='USB device serial')
@click.option('--port', '-p', default=5555, help='TCP port for ADB')
def wireless_setup(device, port):
    """Setup wireless ADB on a USB-connected device."""
    w = WirelessADB()
    
    print_info("Setting up wireless ADB...")
    success, message = w.setup_wireless(device, port)
    
    if success:
        print_success(message)
    else:
        print_error(message)


@wireless.command("pair")
@click.argument('address')
@click.argument('code')
def wireless_pair(address, code):
    """Pair with device using wireless debugging (Android 11+)."""
    w = WirelessADB()
    
    print_info(f"Pairing with {address}...")
    success, message = w.pair(address, code)
    
    if success:
        print_success(message)
    else:
        print_error(message)


@wireless.command("list")
def wireless_list():
    """List wireless devices (connected and saved)."""
    w = WirelessADB()
    devices = w.get_wireless_devices()
    
    if not devices:
        print_warning("No wireless devices")
        return
    
    table = Table(title="Wireless Devices", box=box.SIMPLE)
    table.add_column("Address", style="cyan")
    table.add_column("Status", style="green")
    
    for d in devices:
        status = "[green]Connected[/green]" if d.connected else "[dim]Saved[/dim]"
        table.add_row(d.address, status)
    
    console.print(table)


# ============================================
# Frida Server Commands
# ============================================

@cli.command()
@click.option('--device', '-s', help='Target device serial (required if multiple devices)')
def status(device):
    """Show Frida server status on device."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        if not device:
            devices_list = dm.get_authorized_devices()
            if len(devices_list) > 1:
                print_error("Multiple devices connected. Please specify device with -s/--device")
                return
        print_error("No authorized device found")
        return
    
    print_info(f"Checking Frida status on device: {serial}")
    
    fm = FridaManager(device_serial=serial)
    status_info = fm.get_server_status()
    
    # Create status panel
    if status_info['running']:
        running_status = "[bold green]Running[/bold green]"
        port_status = "[green]Listening[/green]" if status_info['port_listening'] else "[yellow]Not listening[/yellow]"
    else:
        running_status = "[bold red]Not Running[/bold red]"
        port_status = "[dim]N/A[/dim]"
    
    panel_content = f"""
[bold]Server Status:[/bold] {running_status}
[bold]Port 27042:[/bold] {port_status}
[bold]Running Instances:[/bold] {len(status_info['instances'])}
[bold]Installed Servers:[/bold] {len(status_info['installed_servers'])}
    """
    
    console.print(Panel(panel_content, title=f"Device: {serial}", border_style="cyan"))
    
    # Show running instances
    if status_info['instances']:
        table = Table(title="Running Instances", box=box.SIMPLE)
        table.add_column("PID", style="cyan")
        table.add_column("Path", style="dim")
        for inst in status_info['instances']:
            table.add_row(str(inst['pid']), inst['path'])
        console.print(table)
    
    # Show installed servers
    if status_info['installed_servers']:
        console.print("\n[bold]Installed Servers:[/bold]")
        for server in status_info['installed_servers']:
            console.print(f"  [dim]•[/dim] {server}")


@cli.command()
@click.argument('version', required=False)
@click.option('--device', '-s', help='Target device serial')
@click.option('--latest', '-l', is_flag=True, help='Install latest version')
@click.option('--force', '-f', is_flag=True, help='Force reinstall')
def install(version, device, latest, force):
    """Install Frida server on device."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    # Get device info
    info = dm.get_device_info(serial)
    if not info:
        print_error("Failed to get device information")
        return
    
    if not info.is_rooted:
        print_error("Device is not rooted. Frida requires root access.")
        return
    
    # Determine version
    if latest or not version:
        print_info("Fetching latest Frida version...")
        version = get_latest_frida_version()
        if not version:
            print_error("Failed to fetch latest version")
            return
    
    print_info(f"Installing Frida server {version} for {info.frida_architecture}")
    
    fm = FridaManager(device_serial=serial)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installing Frida server...", total=None)
        server_path = fm.install_server(version, info.frida_architecture, force=force)
    
    if server_path:
        print_success(f"Frida server installed at: {server_path}")
    else:
        print_error("Installation failed")


@cli.command()
@click.argument('version', required=False)
@click.option('--device', '-s', help='Target device serial')
@click.option('--latest', '-l', is_flag=True, help='Start latest installed version')
def start(version, device, latest):
    """Start Frida server on device."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    info = dm.get_device_info(serial)
    if not info:
        print_error("Failed to get device information")
        return
    
    if not info.is_rooted:
        print_error("Device is not rooted. Frida requires root access.")
        return
    
    fm = FridaManager(device_serial=serial)
    
    # Check if already running
    if fm.is_server_running():
        print_warning("Frida server is already running")
        servers = fm.get_running_servers()
        for s in servers:
            console.print(f"  [dim]PID:[/dim] {s.pid}")
        
        if not click.confirm("Stop and start new instance?", default=False):
            return
        fm.stop_all_servers()
    
    # Find server path
    if version:
        server_path = fm.is_server_installed(version, info.frida_architecture)
    elif latest:
        installed = fm.list_installed_servers()
        server_path = installed[0] if installed else None
    else:
        # Try to find any installed server
        installed = fm.list_installed_servers()
        if not installed:
            print_error("No Frida server installed. Use 'install' command first.")
            return
        if len(installed) == 1:
            server_path = installed[0]
        else:
            console.print("[bold]Available servers:[/bold]")
            for i, s in enumerate(installed, 1):
                console.print(f"  {i}. {s}")
            choice = click.prompt("Select server", type=int, default=1)
            server_path = installed[choice - 1] if 0 < choice <= len(installed) else None
    
    if not server_path:
        print_error("Frida server not found. Install it first.")
        return
    
    print_info(f"Starting Frida server: {server_path}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Starting server...", total=None)
        success, pid = fm.start_server(server_path)
    
    if success:
        print_success(f"Frida server started (PID: {pid})")
    else:
        print_error("Failed to start Frida server")


@cli.command()
@click.option('--device', '-s', help='Target device serial')
@click.option('--all', '-a', 'stop_all', is_flag=True, help='Stop all Frida instances')
@click.option('--pid', '-p', type=int, help='Specific PID to stop')
def stop(device, stop_all, pid):
    """Stop Frida server on device."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    fm = FridaManager(device_serial=serial)
    servers = fm.get_running_servers()
    
    if not servers:
        print_warning("No Frida server running")
        return
    
    if pid:
        print_info(f"Stopping Frida server PID {pid}")
        success = fm.stop_server(pid)
    else:
        print_info(f"Stopping {len(servers)} Frida server instance(s)")
        success = fm.stop_all_servers()
    
    if success:
        print_success("Frida server stopped")
    else:
        print_error("Failed to stop Frida server")


@cli.command()
@click.option('--device', '-s', help='Target device serial')
def restart(device):
    """Restart Frida server on device."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    fm = FridaManager(device_serial=serial)
    
    # Find current server
    servers = fm.get_running_servers()
    if servers and servers[0].path:
        server_path = servers[0].path
    else:
        installed = fm.list_installed_servers()
        if not installed:
            print_error("No Frida server installed")
            return
        server_path = installed[0]
    
    print_info(f"Restarting Frida server: {server_path}")
    success, pid = fm.restart_server(server_path)
    
    if success:
        print_success(f"Frida server restarted (PID: {pid})")
    else:
        print_error("Failed to restart Frida server")


@cli.command()
@click.option('--limit', '-n', default=10, help='Number of versions to show')
def versions(limit):
    """List available Frida versions."""
    print_info("Fetching available Frida versions...")
    
    version_list = get_available_versions(limit)
    
    if not version_list:
        print_error("Failed to fetch versions")
        return
    
    table = Table(title="Available Frida Versions", box=box.SIMPLE)
    table.add_column("#", style="dim")
    table.add_column("Version", style="cyan")
    
    for i, v in enumerate(version_list, 1):
        if i == 1:
            table.add_row(str(i), f"[bold green]{v}[/bold green] (latest)")
        else:
            table.add_row(str(i), v)
    
    console.print(table)


# ============================================
# Scripts Commands
# ============================================

@cli.group()
def scripts():
    """Frida scripts management."""
    pass


@scripts.command("list")
@click.option('--category', '-c', help='Filter by category')
def scripts_list(category):
    """List available Frida scripts."""
    sm = ScriptManager()
    
    # Built-in scripts
    table = Table(title="Built-in Scripts", box=box.SIMPLE)
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Description", style="dim")
    
    for name, script in BUILTIN_SCRIPTS.items():
        if category and script.category != category:
            continue
        table.add_row(name, script.category, script.description)
    
    console.print(table)
    
    # Custom scripts
    custom = sm.list_custom()
    if custom:
        console.print("\n[bold]Custom Scripts:[/bold]")
        for path in custom:
            console.print(f"  • {path.name}")
    
    # Show categories
    categories = sm.get_categories()
    console.print(f"\n[dim]Categories: {', '.join(categories)}[/dim]")


@scripts.command("show")
@click.argument('name')
def scripts_show(name):
    """Show script content."""
    sm = ScriptManager()
    script = sm.get_builtin(name)
    
    if script:
        console.print(Panel(
            script.content,
            title=f"[cyan]{script.name}[/cyan] - {script.description}",
            border_style="dim"
        ))
    else:
        content = sm.get_custom(name)
        if content:
            console.print(Panel(content, title=name, border_style="dim"))
        else:
            print_error(f"Script '{name}' not found")


@scripts.command("export")
@click.argument('name')
@click.option('--output', '-o', help='Output file path')
def scripts_export(name, output):
    """Export a script to file."""
    sm = ScriptManager()
    path = sm.export_builtin(name, output)
    
    if path:
        print_success(f"Script exported to: {path}")
    else:
        print_error(f"Script '{name}' not found")


# ============================================
# Hook Commands
# ============================================

@cli.group()
def hook():
    """Application hooking helpers."""
    pass


@hook.command("apps")
@click.option('--device', '-s', help='Target device serial')
@click.option('--filter', '-f', 'filter_term', help='Filter packages')
@click.option('--running', '-r', is_flag=True, help='Show only running apps')
def hook_apps(device, filter_term, running):
    """List installed/running applications."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    hooker = AppHooker(device_serial=serial)
    
    if running:
        apps = hooker.get_running_apps()
        table = Table(title="Running Applications", box=box.SIMPLE)
        table.add_column("Package", style="cyan")
        table.add_column("PID", style="yellow")
        
        for app in apps:
            table.add_row(app.package_name, str(app.pid))
    else:
        packages = hooker.list_packages(filter_term)
        table = Table(title="Installed Applications", box=box.SIMPLE)
        table.add_column("#", style="dim")
        table.add_column("Package", style="cyan")
        
        for i, pkg in enumerate(packages[:50], 1):  # Limit to 50
            table.add_row(str(i), pkg)
        
        if len(packages) > 50:
            console.print(f"\n[dim]...and {len(packages) - 50} more[/dim]")
    
    console.print(table)


@hook.command("run")
@click.argument('package')
@click.option('--device', '-s', help='Target device serial')
@click.option('--script', help='Script name or path')
@click.option('--spawn', is_flag=True, help='Spawn new process instead of attach')
@click.option('--bypass', '-b', multiple=True, type=click.Choice(['ssl', 'root', 'debug']), 
              help='Enable bypass (can use multiple)')
def hook_run(package, device, script, spawn, bypass):
    """Hook an application with Frida."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    hooker = AppHooker(device_serial=serial)
    mode = HookMode.SPAWN if spawn else HookMode.ATTACH
    
    if bypass:
        # Use quick bypass
        success, result = hooker.quick_bypass(
            package,
            ssl_bypass='ssl' in bypass,
            root_bypass='root' in bypass,
            debug_bypass='debug' in bypass,
            mode=mode
        )
    elif script:
        success, result = hooker.hook_app(package, script_name=script, mode=mode)
    else:
        success, result = hooker.hook_app(package, mode=mode)
    
    if success:
        print_success("Ready to hook!")
        console.print(f"\n[bold]Run this command:[/bold]")
        console.print(Panel(result, border_style="green"))
    else:
        print_error(result)


@hook.command("start")
@click.argument('package')
@click.option('--device', '-s', help='Target device serial')
def hook_start(package, device):
    """Start an application."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    hooker = AppHooker(device_serial=serial)
    
    print_info(f"Starting {package}...")
    if hooker.start_app(package):
        print_success("Application started")
    else:
        print_error("Failed to start application")


@hook.command("kill")
@click.argument('package')
@click.option('--device', '-s', help='Target device serial')
def hook_kill(package, device):
    """Force stop an application."""
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        print_error("No authorized device found")
        return
    
    hooker = AppHooker(device_serial=serial)
    
    print_info(f"Stopping {package}...")
    if hooker.stop_app(package):
        print_success("Application stopped")
    else:
        print_error("Failed to stop application")


# ============================================
# Doctor Command
# ============================================

@cli.command()
@click.option('--device', '-s', help='Target device serial')
def doctor(device):
    """Diagnose common issues and check system health."""
    print_banner()
    console.print("[bold]Running health checks...[/bold]\n")
    
    doc = Doctor(device_serial=device)
    results = doc.run_all_checks()
    
    # Display results
    for result in results:
        if result.status == CheckStatus.OK:
            icon = "[green]✓[/green]"
        elif result.status == CheckStatus.WARNING:
            icon = "[yellow]![/yellow]"
        elif result.status == CheckStatus.ERROR:
            icon = "[red]✗[/red]"
        else:
            icon = "[dim]○[/dim]"
        
        console.print(f"  {icon} [bold]{result.name}:[/bold] {result.message}")
    
    # Summary
    ok, warning, error, skipped = doc.get_summary()
    console.print(f"\n[bold]Summary:[/bold] {ok} passed, {warning} warnings, {error} errors, {skipped} skipped")
    
    # Show fixes if needed
    fixes = doc.get_fixes()
    if fixes:
        console.print("\n[bold yellow]Suggested Fixes:[/bold yellow]")
        for name, fix in fixes:
            console.print(f"  • [cyan]{name}:[/cyan] {fix}")


# ============================================
# Config Commands
# ============================================

@cli.group()
def config():
    """Configuration management."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = get_config()
    
    table = Table(title="Configuration", box=box.SIMPLE)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="yellow")
    
    for key, value in cfg.to_dict().items():
        table.add_row(key, str(value) if value is not None else "[dim]not set[/dim]")
    
    console.print(table)


@config.command("set")
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set a configuration value."""
    cm = get_config_manager()
    
    # Handle boolean values
    if value.lower() in ('true', 'yes', '1'):
        value = True
    elif value.lower() in ('false', 'no', '0'):
        value = False
    elif value.isdigit():
        value = int(value)
    
    if cm.set(key, value):
        print_success(f"Set {key} = {value}")
    else:
        print_error(f"Unknown configuration key: {key}")


@config.command("init")
def config_init():
    """Initialize configuration file."""
    cm = get_config_manager()
    
    if cm.save():
        print_success(f"Configuration file created")
    else:
        print_error("Failed to create configuration file")


# ============================================
# Interactive Mode
# ============================================

@cli.command()
@click.option('--device', '-s', help='Target device serial')
def interactive(device):
    """Interactive mode for managing Frida server."""
    print_banner()
    
    dm = DeviceManager()
    serial = dm.select_device(device)
    
    if not serial:
        # Show device selection
        devices_list = dm.get_authorized_devices()
        if not devices_list:
            print_error("No authorized devices found")
            return
        
        if len(devices_list) > 1:
            console.print("\n[bold]Select a device:[/bold]")
            for i, d in enumerate(devices_list, 1):
                console.print(f"  {i}. {d.serial} ({d.model or 'Unknown'})")
            
            choice = click.prompt("Device number", type=int, default=1)
            if 0 < choice <= len(devices_list):
                serial = devices_list[choice - 1].serial
            else:
                print_error("Invalid selection")
                return
        else:
            serial = devices_list[0].serial
    
    print_success(f"Selected device: {serial}")
    
    info = dm.get_device_info(serial)
    if info:
        console.print(f"[dim]Model: {info.model} | Android {info.android_version} | {info.frida_architecture}[/dim]")
    
    fm = FridaManager(device_serial=serial)
    
    while True:
        console.print("\n[bold cyan]Actions:[/bold cyan]")
        console.print("  1. Check status")
        console.print("  2. Install Frida server")
        console.print("  3. Start Frida server")
        console.print("  4. Stop Frida server")
        console.print("  5. Restart Frida server")
        console.print("  6. List installed servers")
        console.print("  7. Run health check")
        console.print("  8. List applications")
        console.print("  0. Exit")
        
        choice = click.prompt("\nSelect action", type=int, default=0)
        
        if choice == 0:
            print_info("Goodbye!")
            break
        elif choice == 1:
            status_info = fm.get_server_status()
            running = "[green]Yes[/green]" if status_info['running'] else "[red]No[/red]"
            console.print(f"  Running: {running}")
            console.print(f"  Instances: {len(status_info['instances'])}")
            console.print(f"  Installed: {len(status_info['installed_servers'])}")
        elif choice == 2:
            version = click.prompt("Frida version (or 'latest')", default="latest")
            if version == "latest":
                version = get_latest_frida_version()
            if version and info:
                server_path = fm.install_server(version, info.frida_architecture)
                if server_path:
                    print_success(f"Installed: {server_path}")
                else:
                    print_error("Installation failed")
        elif choice == 3:
            installed = fm.list_installed_servers()
            if installed:
                server_path = installed[0]
                success, pid = fm.start_server(server_path)
                if success:
                    print_success(f"Started (PID: {pid})")
                else:
                    print_error("Failed to start")
            else:
                print_error("No server installed")
        elif choice == 4:
            if fm.stop_all_servers():
                print_success("Stopped all servers")
            else:
                print_error("Failed to stop")
        elif choice == 5:
            installed = fm.list_installed_servers()
            if installed:
                success, pid = fm.restart_server(installed[0])
                if success:
                    print_success(f"Restarted (PID: {pid})")
            else:
                print_error("No server installed")
        elif choice == 6:
            installed = fm.list_installed_servers()
            if installed:
                for s in installed:
                    console.print(f"  • {s}")
            else:
                print_warning("No servers installed")
        elif choice == 7:
            doc = Doctor(device_serial=serial)
            results = doc.run_all_checks()
            for r in results:
                icon = {"ok": "✓", "warning": "!", "error": "✗", "skipped": "○"}[r.status.value]
                console.print(f"  {icon} {r.name}: {r.message}")
        elif choice == 8:
            hooker = AppHooker(device_serial=serial)
            apps = hooker.get_running_apps()
            console.print("\n[bold]Running Applications:[/bold]")
            for app in apps[:20]:
                console.print(f"  • {app.package_name} (PID: {app.pid})")


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
