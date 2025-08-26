import os
import re
import pytest


pytestmark = pytest.mark.e2e


@pytest.mark.skipif(os.getenv("ENABLE_E2E") != "1", reason="E2E disabled unless ENABLE_E2E=1")
def test_create_element_and_note_and_bloom(page):
    # Requires: `pytest -q --headed --browser chromium` and app running at APP_URL
    app_url = os.getenv("APP_URL", "http://localhost:8501")
    page.goto(app_url)

    # Navigate to Elements via top nav button
    page.get_by_role("button", name="Elements").click()
    page.get_by_role("tab", name="Create").click()

    # Fill form - use more specific selectors
    page.get_by_placeholder("e.g., Rose Bush").fill("E2E Test Flower")
    # Streamlit selectbox is an input, not a select element
    type_input = page.get_by_role("combobox", name="Selected flower. Type")
    type_input.click()
    # Target the specific dropdown option
    page.get_by_test_id("stSelectboxVirtualDropdown").get_by_text("flower").click()
    page.get_by_role("button", name="Create Element").click()

    # Manage tab: verify element appears
    page.get_by_role("tab", name="Manage").click()
    page.get_by_text("E2E Test Flower (flower)").first.wait_for()

    # Dashboard via top nav button
    page.get_by_role("button", name="Dashboard").click()
    page.get_by_text("Total elements").first.wait_for()

