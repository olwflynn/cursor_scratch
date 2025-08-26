import db as dbmod


def _use_temp_db(tmp_path):
    dbmod.DATABASE_DIR = str(tmp_path)
    dbmod.DATABASE_PATH = str(tmp_path / "test.db")
    dbmod.init_db()


def test_elements_crud(tmp_path):
    _use_temp_db(tmp_path)
    element_id = dbmod.create_element(
        name="Rose Bush",
        type="flower",
        location="North bed",
        planted_on="2024-03-15",
        variety="Damask",
        image_path="/tmp/rose.png",
    )
    got = dbmod.get_element(element_id)
    assert got and got["name"] == "Rose Bush" and got["type"] == "flower"

    dbmod.update_element(element_id, {"location": "South bed"})
    got2 = dbmod.get_element(element_id)
    assert got2 and got2["location"] == "South bed"

    all_els = dbmod.list_elements()
    assert any(e["id"] == element_id for e in all_els)

    dbmod.delete_element(element_id)
    assert dbmod.get_element(element_id) is None


def test_notes_blooms_stats(tmp_path):
    _use_temp_db(tmp_path)
    el1 = dbmod.create_element(name="Tulip", type="flower")
    el2 = dbmod.create_element(name="Lavender", type="shrub")

    # notes
    dbmod.add_note(el1, "Planted bulbs")
    dbmod.add_note(el1, "First sprout visible")
    notes = dbmod.list_notes(el1)
    assert len(notes) == 2 and notes[0]["note_text"]

    # blooms
    dbmod.add_bloom(el1, start_date="2024-04-10")
    dbmod.add_bloom(el2, start_date="2024-05-01", end_date="2024-05-25")
    blooms1 = dbmod.list_blooms(el1)
    assert len(blooms1) == 1 and blooms1[0]["start_date"] == "2024-04-10"

    stats = dbmod.compute_progress_stats()
    assert stats["total_elements"] == 2
    assert stats["by_type"]["flower"] >= 1
    assert stats["currently_blooming"] >= 1

