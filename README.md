# Ukraine Support Tracker Dashboard

Interactive visualization dashboard showing military, financial, and humanitarian support provided to Ukraine. Built with Shiny for Python, this dashboard provides comprehensive visualizations of bilateral aid commitments, weapon deliveries, and support comparisons across different metrics.

This is a private non-peer reviewed project, and as such, all errors are entirely my own.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for dependency management
- DuckDB database with Ukraine support data
- Git (for version control)

## Setup

### 1. Environment Setup

First, install uv, a fast Python package installer:

```bash
# On Windows
pip install uv

# On Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Clone the repository and set up the development environment:

```bash
# Clone the repository
git clone <repository-url>
cd ukraine-support-tracker

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies (production)
uv sync

# Install with development dependencies
uv sync --extra dev

# Install all optional dependencies
uv sync --all-extras
```

### 2. Database Setup

The project contains a separate section apart from the Dashboard to ensure replicability of data engineering, namely an ETL pipeline with a separate config.yaml in

```
./Code/DataPipeline
```

where a specific short [readme](/Code/DataPipeline/pipeline-readme.md) is available as well.
This is done to enable constant updating by simply replacing the data source excel sheet, deleting the current duckdb and rerunning the pipeline. The separation of instruction and code into yaml and python file was done enable easy configuration of the data pipeline without requiring intense familiarity with python.

Ensure your DuckDB database is properly configured:

1. Verify the database path in `config.py`:

```python
DB_PATH = os.path.join(os.getcwd(), "Data", "ukrainesupporttracker.db")
```

2. The database should contain the following tables:
   - `c_allocated_over_time` - Time series data
   - `e_allocations_refugees_€` - Country-level allocations
   - `f_bilateral_allocations_gdp_pct` - GDP-relative metrics
   - `d_allocations_vs_commitments` - Commitment tracking
   - See `queries.py` for complete table list and schema details

## Running the App

Start the development server:

```bash
shiny run app.py
```

or with specific host and port:

```bash
shiny run app.py --host 0.0.0.0 --port 8000
```

Visit <http://localhost:8000> in your browser.

## Project Structure

```
.
├── app.py                 # Main application entry point
├── config.py             # Configuration settings and color schemes
├── colorutilities.py     # Color manipulation utilities
├── requirements.txt      # Project dependencies
├── server/
│   ├── database.py      # Database connection and query functions
│   └── queries.py       # SQL query definitions
└── ui/
    ├── main.py          # Main UI layout
    ├── pages/
    │   ├── about.py               # About page content
    │   ├── comparisons_page.py    # Historical comparisons
    │   ├── countrywise_page.py    # Country-specific analysis
    │   ├── financial_page.py      # Financial aid analysis
    │   ├── landing_page.py        # Main dashboard page
    │   ├── timeseries_page.py     # Time series analysis
    │   └── weapons_page.py        # Weapons delivery tracking
    └── cards/
        ├── aid_allocation.py      # Aid allocation visualization
        ├── heavy_weapons.py       # Heavy weapons tracking
        ├── pledge_stock_ratio.py  # Pledge vs stock analysis
        └── weapons_stocks.py      # Weapons inventory tracking
```

## Features

### 1. Geographic Visualization

- Interactive choropleth map showing support distribution
- Toggle between absolute values and GDP-relative metrics
- Configurable support type filtering

### 2. Time Series Analysis

- Monthly and cumulative aid allocation trends
- Breakdown by support type (military, financial, humanitarian)
- Donor group comparisons (US, Europe, Rest of World)

### 3. Country-specific Analysis

- Detailed bilateral aid breakdowns
- GDP-relative metrics
- Commitment vs. allocation tracking

### 4. Weapons Support Tracking

- Heavy weapons delivery status
- Stock level comparisons
- Pledge-to-stock ratios

### 5. Historical Comparisons

- WW2 Lend-Lease comparisons
- Cold War military expenditure analysis
- Modern conflict support patterns

## Customization

### Adding New Pages

1. Create a new page module in `ui/pages/`:

```python
from shiny import ui
from .cards.new_visualization import NewVisualizationCard

def new_page_ui():
    return ui.page_fillable(
        ui.panel_title("New Page"),
        NewVisualizationCard.ui()
    )
```

2. Register in `main.py`:

```python
ui.nav_panel("New Page", new_page_ui())
```

### Adding New Visualizations

1. Create new card component in `ui/cards/`:

```python
class NewVisualizationCard:
    @staticmethod
    def ui():
        return ui.card(
            ui.card_header("New Visualization"),
            output_widget("new_viz_plot")
        )
```

2. Implement server logic:

```python
class NewVisualizationServer:
    def __init__(self, input, output, session):
        self.input = input
        self.output = output
        self.session = session
        
    def register_outputs(self):
        @self.output
        @render_widget
        def new_viz_plot():
            return self.create_plot()
```

### Modifying Queries

1. Define new queries in `server/queries.py`:

```python
NEW_QUERY = """
    SELECT column1, column2
    FROM table_name
    WHERE condition
    ORDER BY column1
"""
```

2. Update database functions in `server/database.py`:

```python
def load_new_data():
    return load_data_from_table(NEW_QUERY)
```

### Color Schemes

Update color definitions in `config.py`:

```python
COLOR_PALETTE = {
    "military": "#6B8E23",
    "financial": "#048BA8",
    "humanitarian": "#FFA500",
    "refugee": "#0072BC",
    "custom_category": "#HEX_CODE"
}
```

## Data Updates

The dashboard reads from a DuckDB database that should be updated through a separate ETL pipeline. The database schema includes:

1. Time series tables:
   - Monthly allocations
   - Cumulative totals
   - Aid type breakdowns

2. Country-level metrics:
   - Bilateral aid amounts
   - GDP-relative calculations
   - Refugee cost estimations

3. Weapons tracking:
   - Delivery status
   - Stock levels
   - Pledge tracking

## Performance Considerations

- Use reactive calculations for data filtering
- Implement efficient SQL queries with proper indexing
- Consider caching for frequently accessed data
- Monitor memory usage with large datasets

## Deployment

For production deployment, refer to the [Shiny for Python deployment documentation](https://shiny.posit.co/py/docs/deploy.html).

Common deployment options include:

- Posit Connect
- ShinyServ
- Docker containers
- Cloud platforms (AWS, GCP, Azure)

## Troubleshooting

Common issues and solutions:

1. Database connection errors:
   - Verify DB_PATH in config.py
   - Check file permissions
   - Ensure DuckDB version compatibility

2. Visualization not rendering:
   - Check browser console for errors
   - Verify data availability
   - Review plotly version compatibility

3. Memory issues:
   - Implement data pagination
   - Optimize query performance
   - Increase server resources

## For Economists: Software Engineering Practices in Research

This project demonstrates several software engineering practices that can significantly improve economic research workflows. This section explains these practices and their benefits for economists interested in applying similar approaches.

### 1. Separation of Concerns and Modular Architecture

**What it is:** The project separates data processing (`Code/DataPipeline/`) from visualization (`Code/Shiny/`) and configuration from implementation.

**Why it matters for economists:**
- **Reproducibility:** Each component can be updated independently without breaking others
- **Collaboration:** Multiple researchers can work on different parts simultaneously
- **Maintenance:** Easier to fix bugs or update methods in isolated components

**Implementation example:** See `Code/DataPipeline/pipeline_config.yaml:1-50` for configuration-driven ETL that allows economists to modify data processing without touching code.

### 2. Configuration-Driven Development

**What it is:** Critical parameters and settings are externalized to configuration files (YAML, TOML) rather than hardcoded in scripts.

**Benefits for research:**
- **Parameter sweeps:** Easy to test different assumptions or methodologies
- **Documentation:** Configuration files serve as explicit documentation of research choices
- **Replication:** Other researchers can replicate exactly by using the same config

**Key files:**
- `Code/DataPipeline/pipeline_config.yaml` - Data processing parameters
- `pyproject.toml:124-234` - Project dependencies and tool configurations

### 3. Dependency Management and Virtual Environments

**What it is:** Using tools like `uv` and `pyproject.toml` to explicitly track all software dependencies and versions.

**Critical for economics research:**
- **Replication crisis mitigation:** Exact package versions ensure identical computational environments
- **Collaboration:** Team members get identical software setups
- **Long-term preservation:** Future researchers can recreate the exact environment

**Implementation:** The `pyproject.toml:26-67` specifies exact dependency versions, while `uv` provides fast, deterministic environment creation.

### 4. Extract-Transform-Load (ETL) Pipeline Design

**What it is:** Structured approach to data processing with clear stages: extraction from sources, transformation/cleaning, and loading into analysis-ready formats.

**Value for economists:**
- **Transparency:** Each data transformation step is explicit and auditable
- **Efficiency:** Incremental updates when new data arrives
- **Quality assurance:** Built-in validation at each stage

**Implementation:** See `Code/DataPipeline/ETL.py:1-200` for a comprehensive ETL implementation with monitoring and validation.

### 5. Version Control with Git

**What it is:** Systematic tracking of all changes to code, data configurations, and documentation.

**Research benefits:**
- **Experiment tracking:** Each research iteration is preserved
- **Collaboration:** Multiple researchers can contribute without conflicts
- **Paper trail:** Complete history of methodological decisions

**Best practices demonstrated:**
- Atomic commits with descriptive messages
- Branching for experimental features
- `.gitignore` to exclude temporary and sensitive files

### 6. Documentation as Code

**What it is:** Documentation written in markdown and maintained alongside code, ensuring it stays current.

**Why it's essential:**
- **Onboarding:** New team members or reviewers can quickly understand the project
- **Methods section:** README serves as a draft for paper methodology
- **Future self:** You'll thank yourself for documenting complex decisions

**Examples:**
- This README provides comprehensive setup and usage instructions
- `Code/DataPipeline/pipeline-readme.md` documents ETL-specific processes
- Inline code documentation follows consistent standards

### 7. Testing and Validation

**What it is:** Automated checks to ensure code correctness and data quality.

**Research applications:**
- **Data validation:** Ensure datasets meet expected properties
- **Method verification:** Confirm statistical procedures work correctly
- **Regression testing:** Prevent bugs when updating code

**Implementation notes:**
- `Code/DataPipeline/pipeline_validation.py` provides data quality checks
- `pyproject.toml:206-219` configures testing frameworks
- Pre-commit hooks (`.pre-commit-config.yaml`) ensure code quality

### 8. Package and Environment Management

**What it is:** Treating research code as a proper software package with clear dependencies and installation procedures.

**Advantages:**
- **Distribution:** Easy sharing with colleagues or journal reviewers
- **Installation:** Simple setup on new machines or cloud platforms
- **Professionalism:** Demonstrates software engineering competency to non-economists

**Key concepts:**
- `pyproject.toml` defines the project as an installable package
- Optional dependencies (`[dev]`, `[jupyter]`) for different use cases
- Entry points for command-line tools

### 9. Continuous Integration Concepts

**What it is:** Automated testing and validation whenever code changes.

**Research value:**
- **Quality assurance:** Catch errors before they affect results
- **Confidence:** Know that changes don't break existing functionality
- **Standards:** Enforce coding standards across team members

**Setup:** Pre-commit hooks and ruff configuration ensure consistent code quality.

### Getting Started with These Practices

For economists interested in adopting these practices:

1. **Start small:** Begin with configuration files for your main parameters
2. **Use version control:** Start tracking your code with Git immediately
3. **Document everything:** Write clear README files for your projects
4. **Modularize:** Separate data processing from analysis scripts
5. **Specify dependencies:** Use requirements.txt or pyproject.toml

### Recommended Learning Resources

- **Git for economists:** [Software Carpentry Git Tutorial](https://swcarpentry.github.io/git-novice/)
- **Python packaging:** [Python Packaging Authority Guide](https://packaging.python.org/)
- **Project structure:** [Cookiecutter Data Science](https://drivendata.github.io/cookiecutter-data-science/)
- **Configuration management:** [Hydra framework](https://hydra.cc/) for complex parameter management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT

## Acknowledgments

### Data sourcing

This little app would not be possible without the wonderful and necessary work of the [Ukraine Support Tracker](https://www.ifw-kiel.de/topics/war-against-ukraine/ukraine-support-tracker/) Team who do the actual work of data collection and compilation. Their effort is the foundation on which this whole side project is build upon. My gratitude for their contribution to the public commons is immense. In case your interest is peaked, [here is the accompanying working paper](https://www.ifw-kiel.de/publications/the-ukraine-support-tracker-which-countries-help-ukraine-and-how-20852/).

# Software Credits

## Core Web Framework and Visualization

### Shiny for Python

- Website: <https://shiny.posit.co/py/>
- GitHub: <https://github.com/posit-dev/py-shiny>
- Citation:

```bibtex
@software{shiny_python_2024,
  author = {Posit PBC},
  title = {Shiny for Python},
  year = {2024},
  publisher = {Posit PBC},
  url = {https://shiny.posit.co/py/}
}
```

### Plotly

- Website: <https://plotly.com/python/>
- GitHub: <https://github.com/plotly/plotly.py>
- Citation:

```bibtex
@software{plotly_2024,
  author = {Plotly Technologies Inc.},
  title = {Plotly Python Open Source Graphing Library},
  year = {2024},
  publisher = {Plotly Technologies Inc.},
  url = {https://plotly.com/python/}
}
```

## Database and Data Processing

### DuckDB

- Website: <https://duckdb.org/>
- GitHub: <https://github.com/duckdb/duckdb>
- Citation:

```bibtex
@article{duckdb2019,
  title={DuckDB: an Embeddable Analytical Database},
  author={Raasveldt, Mark and M{\"u}hleisen, Hannes},
  journal={Proceedings of the 2019 International Conference on Management of Data},
  year={2019},
  publisher={ACM}
}
```

### Pandas

- Website: <https://pandas.pydata.org/>
- GitHub: <https://github.com/pandas-dev/pandas>
- Citation:

```bibtex
@software{reback2020pandas,
    author = {The pandas development team},
    title = {pandas-dev/pandas: Pandas},
    year = {2024},
    publisher = {Zenodo},
    url = {https://doi.org/10.5281/zenodo.3509134}
}
```

### NumPy

- Website: <https://numpy.org/>
- GitHub: <https://github.com/numpy/numpy>
- Citation:

```bibtex
@article{harris2020array,
  title={Array programming with {NumPy}},
  author={Harris, Charles R. and Millman, K. Jarrod and van der Walt, Stéfan J. and Gommers, Ralf and Virtanen, Pauli and Cournapeau, David and Wieser, Eric and Taylor, Julian and Berg, Sebastian and Smith, Nathaniel J. and others},
  journal={Nature},
  volume={585},
  number={7825},
  pages={357--362},
  year={2020},
  publisher={Nature Publishing Group}
}
```

## Development Tools

### Claude.ai

- Website: <https://claude.ai>

### UV

- Website: <https://github.com/astral-sh/uv>
- GitHub: <https://github.com/astral-sh/uv>

### Jupyter

- Website: <https://jupyter.org/>
- GitHub: <https://github.com/jupyter>
- Citation:

```bibtex
@article{kluyver2016jupyter,
  title={Jupyter Notebooks-a publishing format for reproducible computational workflows},
  author={Kluyver, Thomas and Ragan-Kelley, Benjamin and P{\'e}rez, Fernando and Granger, Brian and Bussonnier, Matthias and Frederic, Jonathan and Kelley, Kyle and Hamrick, Jessica and Grout, Jason and Corlay, Sylvain and others},
  journal={Positioning and Power in Academic Publishing: Players, Agents and Agendas},
  pages={87--90},
  year={2016}
}
```

## Python Web Dependencies

### Starlette

- Website: <https://www.starlette.io/>
- GitHub: <https://github.com/encode/starlette>

### Uvicorn

- Website: <https://www.uvicorn.org/>
- GitHub: <https://github.com/encode/uvicorn>

### Anyio

- GitHub: <https://github.com/agronholm/anyio>

## UI Dependencies

### htmltools

- GitHub: <https://github.com/posit-dev/htmltools>

### shinywidgets

- GitHub: <https://github.com/posit-dev/py-shinywidgets>

## Development Dependencies

### Ruff

- Website: <https://beta.ruff.rs/docs/>
- GitHub: <https://github.com/astral-sh/ruff>

## Data Types and Validation

### Attrs

- Website: <https://www.attrs.org/>
- GitHub: <https://github.com/python-attrs/attrs>

### jsonschema

- Website: <https://python-jsonschema.readthedocs.io/>
- GitHub: <https://github.com/python-jsonschema/jsonschema>

## License Information

All listed packages are used under their respective licenses. Please refer to each package's documentation for specific license details.

## Contact

You can contact my via the usual means from GitHub, for other ways visit [my Website](www.infornomics.de).
