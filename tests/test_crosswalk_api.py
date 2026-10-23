"""Read-only GET /crosswalk against the real NIST database (no LLM, no retrieval)."""
import pytest
from fastapi.testclient import TestClient

from controlshift.api.app import create_app
from controlshift.api.services import Services
from controlshift.generation.config import Settings


@pytest.fixture(scope="module")
def client(real_db):
    svc = Services(real_db[0], Settings(db_path=real_db[0]), None, "none", None, [])
    with TestClient(create_app(lambda: svc), raise_server_exceptions=False) as c:
        yield c


def rows(r):
    return [e["excel_row"] for e in r.json()["entries"]]


def test_all_rows_in_workbook_order_with_explicit_counts(client):
    body = client.get("/crosswalk").json()
    assert body["total"] == body["count"] == len(body["entries"]) == 205
    assert body["direction"] == "CSF 2.0 (focal) -> CSF 1.1 (reference)"
    r = [e["excel_row"] for e in body["entries"]]
    assert r == sorted(r) and len(set(r)) == 205
    assert sum(body["type_counts"].values()) == 205
    assert client.get("/crosswalk").json() == body  # deterministic


def test_source_metadata_is_preserved(client):
    e = client.get("/crosswalk", params={"focal": "GV.SC-03"}).json()["entries"][0]
    assert e["sheet"] == "Relationships" and e["source_file"] == "nist_csf_transition.xlsx"
    assert (e["focal_version"], e["reference_version"]) == ("2.0", "1.1")
    assert e["focal_original_id"] == "GV.SC-03" and e["focal_description"]
    assert e["strength"] is None and e["mapping_type"] in {"mapped", "new_in_2_0", "unmapped"}


def test_gv_sc_03_has_rows_25_and_26_independent(client):
    body = client.get("/crosswalk", params={"focal": "gv.sc-03"}).json()
    assert [e["excel_row"] for e in body["entries"]] == [25, 26]
    r25, r26 = body["entries"]
    assert (r25["reference_element_id"], r25["reference_original_id"]) == ("ID.SC-02", "ID.SC-2")
    assert r25["mapping_type"] == "mapped"
    assert r26["reference_element_id"] is None and r26["reference_original_id"] is None
    assert r26["reference_description"] is None
    assert r26["comments"] == "Conceptually new in 2.0" and r26["mapping_type"] == "new_in_2_0"


def test_id_im_03_has_seven_rows(client):
    assert len(rows(client.get("/crosswalk", params={"focal": "ID.IM-03"}))) == 7


def test_reverse_reference_filter_accepts_either_spelling(client):
    a = client.get("/crosswalk", params={"reference": "ID.SC-02"}).json()
    b = client.get("/crosswalk", params={"reference": "id.sc-2"}).json()
    assert a == b and 25 in rows(client.get("/crosswalk", params={"reference": "ID.SC-2"}))
    assert all(e["reference_element_id"] == "ID.SC-02" for e in a["entries"])


def test_unreferenced_1_1_element_returns_nothing_and_no_assertion(client):
    body = client.get("/crosswalk", params={"reference": "RC.CO-02"}).json()
    assert body["total"] == 0 and body["entries"] == []
    assert "remov" not in str(body).lower()


def test_type_filter_and_counts_ignore_the_type_filter(client):
    allc = client.get("/crosswalk").json()["type_counts"]
    new = client.get("/crosswalk", params={"type": "new_in_2_0"}).json()
    assert new["total"] == allc["new_in_2_0"] and new["type_counts"] == allc
    assert all(e["mapping_type"] == "new_in_2_0" and e["reference_element_id"] is None for e in new["entries"])
    mapped = client.get("/crosswalk", params={"type": "mapped"}).json()
    assert all(e["reference_element_id"] for e in mapped["entries"])


def test_search_over_ids_text_and_comments_and_row_number(client):
    assert {25, 26} <= set(rows(client.get("/crosswalk", params={"q": "gv.sc-03"})))
    comment = client.get("/crosswalk", params={"q": "Conceptually new"}).json()
    assert 26 in [e["excel_row"] for e in comment["entries"]]
    assert 25 in rows(client.get("/crosswalk", params={"q": "25"}))
    assert rows(client.get("/crosswalk", params={"q": "zzzzqqqq"})) == []
    assert client.get("/crosswalk", params={"q": "%"}).json()["total"] < 205  # wildcards are literal
    both = client.get("/crosswalk", params={"focal": "GV.SC-03", "type": "mapped"})
    assert rows(both) == [25]


def test_pagination_is_stable(client):
    full = rows(client.get("/crosswalk"))
    p1 = client.get("/crosswalk", params={"limit": 50}).json()
    p2 = client.get("/crosswalk", params={"limit": 50, "offset": 50}).json()
    assert (p1["total"], p1["count"], p2["offset"]) == (205, 50, 50)
    assert rows(client.get("/crosswalk", params={"limit": 50, "offset": 200})) == full[200:]
    assert [e["excel_row"] for e in p1["entries"]] + [e["excel_row"] for e in p2["entries"]] == full[:100]


@pytest.mark.parametrize("params", [
    {"focal": "nonsense"}, {"reference": "GV.SC-003"}, {"type": "other"}, {"limit": 0},
    {"limit": 251}, {"offset": -1}, {"q": "x" * 201}])
def test_invalid_queries_use_the_error_envelope(client, params):
    r = client.get("/crosswalk", params=params)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"
    assert r.json()["error"]["details"]


def test_read_only(client):
    assert client.post("/crosswalk", json={}).status_code == 405
