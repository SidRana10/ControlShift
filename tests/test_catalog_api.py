"""Read-only /catalog routes against the real NIST database (no LLM, no retrieval)."""
import pytest
from fastapi.testclient import TestClient

from controlshift.api.app import create_app
from controlshift.api.catalog import summarize_crosswalk
from controlshift.api.services import Services
from controlshift.generation.config import Settings


@pytest.fixture(scope="module")
def client(real_db):
    svc = Services(real_db[0], Settings(db_path=real_db[0]), None, "none", None, [])
    with TestClient(create_app(lambda: svc), raise_server_exceptions=False) as c:
        yield c


def ids(r):
    return [e["element_id"] for e in r.json()["elements"]]


def test_versions_metadata_and_counts(client):
    body = client.get("/catalog/versions").json()
    by = {v["version"]: v for v in body["versions"]}
    assert list(by) == ["1.1", "2.0"]
    assert by["2.0"]["name"] == "NIST Cybersecurity Framework 2.0"
    assert by["2.0"]["counts"] == {"function": 6, "category": 22, "subcategory": 106}
    assert by["1.1"]["counts"] == {"function": 5, "category": 23, "subcategory": 108}
    assert by["1.1"]["total_elements"] == 136
    assert by["1.1"]["source_document"]["source_file"] == "nist_csf_1_1.pdf"
    assert len(by["2.0"]["source_document"]["sha256"]) == 64


def test_list_all_and_stable_order(client):
    r = client.get("/catalog/elements").json()
    assert r["count"] == 270 == len(r["elements"])
    keys = [(e["version"], e["element_id"]) for e in r["elements"]]
    assert keys == sorted(keys) and client.get("/catalog/elements").json() == r


def test_filters(client):
    r = client.get("/catalog/elements", params={"version": "2.0", "level": "function"})
    assert ids(r) == ["DE", "GV", "ID", "PR", "RC", "RS"]
    r = client.get("/catalog/elements", params={"version": "2.0", "function": "gv"})
    assert {e["function_id"] for e in r.json()["elements"]} == {"GV"}
    assert r.json()["count"] == 1 + 6 + sum(e["level"] == "subcategory" for e in r.json()["elements"])
    r = client.get("/catalog/elements", params={"version": "2.0", "category": "GV.SC"})
    assert ids(r)[0] == "GV.SC" and "GV.SC-03" in ids(r)
    assert {e["category_id"] for e in r.json()["elements"]} == {"GV.SC"}
    r = client.get("/catalog/elements", params={"version": "1.1", "function": "GV"})
    assert r.json() == {"count": 0, "elements": []}


def test_id_search_exact_partial_and_original_spelling(client):
    r = client.get("/catalog/elements", params={"q": "gv.sc-03"})
    assert ids(r) == ["GV.SC-03"]
    assert "GV.SC-03" in ids(client.get("/catalog/elements", params={"q": "GV.SC"}))
    r = client.get("/catalog/elements", params={"version": "1.1", "q": "PR.AT-1"})
    assert r.json()["elements"][0]["original_id"] == "PR.AT-1"
    assert r.json()["elements"][0]["element_id"] == "PR.AT-01"


def test_text_search_and_wildcards_are_literal(client):
    r = client.get("/catalog/elements", params={"q": "supply chain", "version": "2.0"})
    assert "GV.SC" in ids(r) and "GV.SC-03" in ids(r)
    r = client.get("/catalog/elements", params={"q": "Supply Chain"})
    assert r.json()["count"] > 0
    for wild in ("%", "_", "GV_SC"):
        assert client.get("/catalog/elements", params={"q": wild}).json()["count"] == 0


@pytest.mark.parametrize("params", [
    {"version": "3.0"}, {"level": "section"}, {"function": "GOV"}, {"category": "GV"},
    {"category": "GV.SC-03"}, {"q": "x" * 201}])
def test_invalid_filters(client, params):
    r = client.get("/catalog/elements", params=params)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"


def test_null_names_and_descriptions_are_preserved(client):
    el = {(e["version"], e["element_id"]): e
          for e in client.get("/catalog/elements").json()["elements"]}
    assert el[("2.0", "GV.SC-03")]["name"] is None and el[("2.0", "GV.SC-03")]["description"]
    assert el[("1.1", "DE")]["description"] is None and el[("1.1", "DE")]["name"] == "Detect"
    assert el[("2.0", "GV")]["parent_id"] is None and el[("2.0", "GV")]["category_id"] is None


def test_detail_identity_hierarchy_provenance(client):
    r = client.get("/catalog/elements/2.0/GV.SC-03")
    assert r.status_code == 200
    d = r.json()
    assert d["level"] == "subcategory" and d["name"] is None
    assert d["parent"]["element_id"] == "GV.SC" and d["children"] == []
    p = d["provenance"]
    assert p["source_document"]["source_file"] == "nist_csf_2_0.pdf"
    assert (p["chunk"]["page"], p["chunk"]["printed_page"]) == (22, "17")
    assert p["chunk"]["section"] == "Core > Govern (GV) > GV.SC-03"
    cat = client.get("/catalog/elements/2.0/GV.SC").json()
    assert cat["parent"]["element_id"] == "GV" and "GV.SC-03" in [c["element_id"] for c in cat["children"]]
    fn = client.get("/catalog/elements/2.0/GV").json()
    assert fn["parent"] is None and "GV.SC" in [c["element_id"] for c in fn["children"]]


def test_detail_id_spellings_and_informative_references(client):
    a = client.get("/catalog/elements/1.1/PR.AT-1").json()
    b = client.get("/catalog/elements/1.1/pr.at-01").json()
    assert a == b and a["element_id"] == "PR.AT-01" and a["original_id"] == "PR.AT-1"
    assert a["informative_references"] and all(isinstance(x, str) for x in a["informative_references"])


def test_gv_sc_03_crosswalk_rows_25_and_26(client):
    cw = client.get("/catalog/elements/2.0/GV.SC-03").json()["crosswalk"]
    assert cw["direction"] == "CSF 2.0 (focal) -> CSF 1.1 (reference)"
    assert (cw["lookup"], cw["queried_role"]) == ("forward", "focal")
    rows = {e["excel_row"]: e for e in cw["entries"]}
    assert sorted(rows) == [25, 26]
    assert rows[25]["reference_element_id"] == "ID.SC-02" and rows[25]["mapping_type"] == "mapped"
    assert rows[25]["comments"] is None and rows[25]["sheet"] == "Relationships"
    assert rows[26]["reference_element_id"] is None and rows[26]["reference_description"] is None
    assert rows[26]["comments"] == "Conceptually new in 2.0" and rows[26]["mapping_type"] == "new_in_2_0"
    s = cw["summary"]
    assert s["derived"] is True and s["status"] == "mapped_and_new_in_2_0"
    assert (s["mapped_row_count"], s["new_in_2_0_row_count"], s["excel_rows"]) == (1, 1, [25, 26])


def test_one_to_many_rows_are_not_merged(client):
    cw = client.get("/catalog/elements/2.0/ID.IM-03").json()["crosswalk"]
    assert len(cw["entries"]) == 7 == len({e["excel_row"] for e in cw["entries"]})
    assert cw["summary"]["excel_rows"] == [e["excel_row"] for e in cw["entries"]]


def test_reverse_lookup_for_1_1(client):
    cw = client.get("/catalog/elements/1.1/ID.SC-02").json()["crosswalk"]
    assert (cw["lookup"], cw["queried_role"]) == ("reverse", "reference")
    assert {25, 27} <= {e["excel_row"] for e in cw["entries"]}
    assert all(e["reference_element_id"] == "ID.SC-02" for e in cw["entries"])
    assert cw["summary"]["status"] == "mapped_only"


def test_new_in_2_0_only_and_no_crosswalk_reference(client, real_db):
    from controlshift.store.queries import KnowledgeStore

    with KnowledgeStore(real_db[0]) as s:
        new_only = [e for e in s.controls_flagged_new_in_2_0()
                    if e["element_id"] not in {m["focal_element_id"] for m in
                                                s.conn.execute("SELECT focal_element_id FROM crosswalk_mapping"
                                                               " WHERE mapping_type='mapped'")}]
        orphan = s.controls_without_later_mapping()[0]
    assert new_only
    n = client.get(f"/catalog/elements/2.0/{new_only[0]['element_id']}").json()["crosswalk"]
    assert n["summary"]["status"] == "new_in_2_0_only" and n["entries"][0]["reference_element_id"] is None
    o = client.get(f"/catalog/elements/1.1/{orphan['element_id']}").json()["crosswalk"]
    assert o["entries"] == [] and o["summary"]["status"] == "no_crosswalk_reference"
    assert "removed" in o["summary"]["note"] and "not a statement" in o["summary"]["note"]


def test_summary_helper_unclassified():
    assert summarize_crosswalk([{"mapping_type": "unmapped", "excel_row": 9}])["status"] == "unclassified"


@pytest.mark.parametrize("path", ["/catalog/elements/2.0/ZZ.QQ-99", "/catalog/elements/1.1/GV",
                                  "/catalog/elements/2.0/not%20an%20id", "/catalog/elements/2.0/GV.SC-003"])
def test_unknown_ids_return_404_envelope(client, path):
    r = client.get(path)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found" and r.json()["error"]["details"] is None


def test_unknown_version_is_validation_error(client):
    r = client.get("/catalog/elements/3.0/GV")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_request"
