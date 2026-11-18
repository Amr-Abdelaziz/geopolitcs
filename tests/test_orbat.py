"""Tests for Order of Battle (ORBAT) Service and REST API."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from services.orbat.orbat_service import OrbatService


def test_orbat_service_data_integrity():
    """Verify ORBAT units for Egypt, Libya, and Israel are seeded properly."""
    service = OrbatService()
    
    # 1. Total count check
    tree_all = service.get_orbat_tree(country="All")
    assert tree_all.total_units >= 20
    assert len(tree_all.roots) >= 3  # EAF-GHQ, LNA-GHQ, GNU-GHQ, IDF-GENERAL-STAFF

    # 2. Egypt Hierarchy
    tree_egy = service.get_orbat_tree(country="Egypt")
    assert tree_egy.total_units >= 10
    root_egy = [r for r in tree_egy.roots if r.id == "EAF-GHQ"]
    assert len(root_egy) == 1
    # Check that children exist (Western Zone, 2nd Army, 3rd Army, etc.)
    sub_ids = [sub.id for sub in root_egy[0].sub_units]
    assert "EAF-WEST-ZONE" in sub_ids
    assert "EAF-2ND-ARMY" in sub_ids
    assert "EAF-3RD-ARMY" in sub_ids

    # 3. Libya Hierarchy
    tree_lby = service.get_orbat_tree(country="Libya")
    assert tree_lby.total_units >= 5
    lna_root = [r for r in tree_lby.roots if r.id == "LNA-GHQ"]
    assert len(lna_root) == 1
    assert any(sub.id == "LNA-BDE-106" for sub in lna_root[0].sub_units)

    # 4. Israel Hierarchy
    tree_isr = service.get_orbat_tree(country="Israel")
    assert tree_isr.total_units >= 5
    idf_root = [r for r in tree_isr.roots if r.id == "IDF-GENERAL-STAFF"]
    assert len(idf_root) == 1
    assert any(sub.id == "IDF-SOUTH-CMD" for sub in idf_root[0].sub_units)


def test_orbat_filtering_and_search():
    """Verify branch filtering and text search in ORBAT service."""
    service = OrbatService()

    # Branch filter
    naval_units = service.get_orbat_tree(branch="Naval")
    assert naval_units.total_units >= 2
    assert all(u.branch == "Naval" for u in naval_units.flat_units)

    # Search filter
    abrams_search = service.get_orbat_tree(search="Abrams")
    assert abrams_search.total_units >= 2

    # Unit dossier lookup
    unit = service.get_unit("EAF-WEST-ZONE")
    assert unit is not None
    assert "سيدي براني" in unit.hq_location
    assert len(unit.equipment) >= 2


@pytest.mark.asyncio
async def test_api_orbat_tree_endpoint():
    """Verify GET /api/orbat returns valid OrbatTreeResponse."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default all
        res = await client.get("/api/orbat")
        assert res.status_code == 200
        data = res.json()
        assert "roots" in data
        assert data["total_units"] >= 20

        # Filter by country=Egypt
        res_egy = await client.get("/api/orbat?country=Egypt")
        assert res_egy.status_code == 200
        data_egy = res_egy.json()
        assert data_egy["country"] == "Egypt"
        assert len(data_egy["roots"]) >= 1


@pytest.mark.asyncio
async def test_api_orbat_unit_dossier_endpoint():
    """Verify GET /api/orbat/{unit_id} returns unit details or 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Existing unit
        res = await client.get("/api/orbat/EAF-BASE-JULY3")
        assert res.status_code == 200
        unit = res.json()
        assert unit["id"] == "EAF-BASE-JULY3"
        assert "3 يوليو" in unit["name_ar"]
        assert unit["branch"] == "Naval"

        # Non-existing unit
        res_404 = await client.get("/api/orbat/UNKNOWN-UNIT-XYZ")
        assert res_404.status_code == 404
