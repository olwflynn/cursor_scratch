import os
import pytest


pytestmark = pytest.mark.e2e


@pytest.mark.skipif(os.getenv("ENABLE_E2E") != "1", reason="E2E disabled unless ENABLE_E2E=1")
def test_create_element_and_note_and_bloom(page):
    # Requires: `pytest -q --headed --browser chromium` and app running at APP_URL
    app_url = os.getenv("APP_URL", "http://localhost:8501")
    page.goto(app_url)

    # Navigate to Elements tab
    page.get_by_role("tab", name="Elements").click()
    page.get_by_role("tab", name="Create").click()

    # Fill form
    page.get_by_label("Name").fill("E2E Test Flower")
    page.get_by_label("Type").select_option(label="flower")
    page.get_by_label("Generate a sample image if none uploaded").check()
    page.get_by_role("button", name="Create Element").click()

    # Manage tab
    page.get_by_role("tab", name="Manage").click()
    page.get_by_text("E2E Test Flower (flower)").first.wait_for()

    # Add a note
    page.get_by_role("button", name="Notes").click()
    page.get_by_label("Add note").fill("E2E note")
    page.get_by_role("button", name="Add").click()

    # Add a bloom
    page.get_by_role("button", name="Bloom tracker").click()
    page.get_by_label("Start date").fill("2025-05-01")
    page.get_by_role("button", name="Add bloom").click()

    # Dashboard
    page.get_by_role("tab", name="Dashboard").click()
    page.get_by_text("Total elements").first.wait_for()

