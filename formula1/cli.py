 # formula1/cli.py

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import predictor

# --- Helper for styled output ---
console = Console()

def print_welcome():
    """Prints the welcome message when 'formula1' is run without args."""
    console.print(Panel(
        Text(
            "Welcome to the F1 Grand Prix Predictor!\n\n"
            "This tool provides a fun, data-driven prediction for the upcoming F1 race.\n\n"
            "Usage:\n"
            "  $ formula1 [GP_NAME]\n\n"
            "Examples:\n"
            "  $ formula1          (gets the very next GP)\n"
            "  $ formula1 monaco     (gets the Monaco GP)\n"
            "  $ formula1 silverstone  (gets the British GP)\n"
            "!!!previous race's results are not included in the prediction!!!",
            justify="center"
        ),
        title="[bold magenta]🏎️ F1 Predictor[/bold magenta]",
        border_style="green"
    ))

def print_prediction(prediction):
    """Prints the prediction in a nicely formatted table."""
    if prediction.get("error"):
        console.print(f"[bold red]Error:[/bold red] {prediction['error']}")
        return

    title = f"Prediction for the {prediction['event_name']}"
    subtitle = f"{prediction['location']} | [italic]{prediction['tidbit']}[/italic]"
    
    panel_content = Table(box=None, show_header=False, expand=True)
    panel_content.add_column(style="bold cyan")
    panel_content.add_column()
    
    # Podium Favorites
    panel_content.add_row("[🏆] Podium Favorites", "")
    for podium_position, driver in enumerate(prediction['podium_favorites'], start=1):
        panel_content.add_row(
            f"  P{podium_position}",  # Use the counter for the P-number
            f"{driver['name']} - {driver['constructor']} (this year's standing: {driver['position']})"
        )
    panel_content.add_row("", "") # Spacer

    # Dark Horse
    if prediction['dark_horse']:
        dh = prediction['dark_horse']
        panel_content.add_row("-> Dark Horse", f"{dh['name']} ({dh['constructor']})")
    
    # Potential Surprise
    if prediction['potential_surprise']:
        ps = prediction['potential_surprise']
        panel_content.add_row("-> Potential Surprise", f"{ps['name']} ({ps['constructor']})")

    console.print(Panel(
        panel_content,
        title=title,
        subtitle=subtitle,
        border_style="magenta"
    ))
    console.print("\n[italic yellow]Disclaimer: This prediction is based on current championship standings and is for entertainment purposes only.[/italic yellow]")


@click.command()
@click.argument('gp_name', required=False)
def main(gp_name):
    """
    Predicts the upcoming Formula 1 Grand Prix based on current standings.
    
    You can specify a GP by name (e.g., 'monaco') or run it without arguments
    to get the very next race on the calendar.
    """
    if not gp_name:
        # If no GP name is provided, try to get the next one.
        # But first, show help info if it's the user's first time.
        print_welcome()
        console.print("\n[bold]Getting the next race on the calendar...[/bold]\n")

    
    with console.status("[bold green]Fetching race data...[/bold green]"):
        event_info, error = predictor.get_next_gp(gp_name)
        if error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            return

    with console.status("[bold green]Analyzing driver standings...[/bold green]"):
        standings, error = predictor.get_driver_standings()
        if error:
            console.print(f"[bold red]Error:[/bold red] {error}")
            return

    with console.status("[bold green]Running predictive model...[/bold green]"):
        prediction = predictor.generate_prediction(standings, event_info)

    print_prediction(prediction)


if __name__ == '__main__':
    main()