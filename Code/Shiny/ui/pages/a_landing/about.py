import os
from typing import Any

from config import LAST_UPDATE
from shiny import Session, ui


def landing_page_ui() -> ui.page_fillable:
    """Create the user interface elements for the landing page.

    Returns:
        ui.page_fillable: A Shiny page containing the main layout and overview content.
    """
    # Read the markdown content from file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_path = os.path.join(current_dir, "about.md")
    with open(markdown_path, encoding="utf-8") as f:
        about_content = f.read()

    # Replace the placeholder using format
    formatted_content = about_content.format(LAST_UPDATE=LAST_UPDATE)

    return ui.page_fillable(
        ui.div(
            {"class": "container-fluid"},
            ui.div(
                {"class": "row mb-4"},
                ui.div({"class": "col-12"}, ui.markdown(formatted_content)),
            ),
        )
    )


class LandingPageServer:
    """Server logic for the landing page."""

    def __init__(self, input: Any, output: Any, session: Session):
        """Initialize the landing page server.

        Args:
            input: Shiny input object.
            output: Shiny output object.
            session: Shiny session object.
        """
        self.input = input
        self.output = output
        self.session = session

    def initialize(self) -> None:
        """Initialize server-side components."""
        pass  # Add any necessary initializations here
