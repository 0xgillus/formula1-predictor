 # 🏎️ F1 Grand Prix Predictor

A fun command-line tool that provides a data-driven prediction for the upcoming F1 race based on current championship standings.

## Features

- Get predictions for the very next race automatically.
- Look up predictions for a specific Grand Prix by name (e.g., `monaco`, `silverstone`).
- Fun, colorful output using Rich.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/0xgillus/formula1-predictor.git
    cd formula1-predictor
    ```

2.  **Install the package:**
    It is highly recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python3 -m venv venv
    source venv/bin/activate

    # Install the tool and its dependencies
    pip install .
    ```
    This will install all required libraries and add the `formula1` command to your path.

## Usage

**Get a prediction for the next upcoming race:**
```bash
formula1
```

**Get a prediction for a specific race by name:**
```bash
formula1 monaco
```
```bash
formula1 silverstone
```
