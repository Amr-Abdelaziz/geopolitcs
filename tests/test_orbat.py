"""Tests for Order of Battle (ORBAT) Service and REST API with GeoConfirmed Logos."""
import pytest
from httpx import ASGITransport, AsyncClient
from apps.api.main import app
from services.orbat.orbat_service import OrbatService


def test_orbat_service_data_integrity():
    """Verify ORBAT units for Egypt and Libya are seeded properly."""
    service = OrbatService()
    
    # 1. Catalogs
    catalogs = service.get_catalogs()
    assert len(catalogs) >= 20
    cat_codes = [c.code for c in catalogs]
    assert "Egypt" in cat_codes
    assert "Libya" in cat_codes
    assert "Israel" in cat_codes
    assert "Russia" in cat_codes
    assert "PalestinianFactions" in cat_codes

    # 2. Egypt Hierarchy
    tree_egy = service.get_orbat_tree(catalog="egypt")
    assert tree_egy.total_units >= 10
    root_egy = [r for r in tree_egy.roots if r.id == "EAF-GHQ"]
    assert len(root_egy) == 1
    sub_ids = [sub.id for sub in root_egy[0].sub_units]
    assert "EAF-WEST-ZONE" in sub_ids
    assert "EAF-2ND-ARMY" in sub_ids
    assert "EAF-3RD-ARMY" in sub_ids

    # Check logos on Egypt root
    assert root_egy[0].logo_url is not None

    # 3. Libya Hierarchy
    tree_lby = service.get_orbat_tree(catalog="libya")
    assert tree_lby.total_units >= 5
    lna_root = [r for r in tree_lby.roots if r.id == "LNA-GHQ"]
    assert len(lna_root) == 1
    assert any(sub.id == "LNA-BDE-106" for sub in lna_root[0].sub_units)


def test_orbat_geoconfirmed_middle_east_and_logos():
    """Verify GeoConfirmed Middle Eastern Factions and Israel catalogs with official logos."""
    service = OrbatService()
    tree_me = service.get_orbat_tree(catalog="middleeasternfactions")
    assert tree_me.total_units >= 5
    assert len(tree_me.roots) >= 1
    root = tree_me.roots[0]

    # Verify that units in tree possess GeoConfirmed logo URLs
    flat_units = tree_me.flat_units
    units_with_logos = [u for u in flat_units if u.logo_url and "geoconfirmed.org" in u.logo_url]
    assert len(units_with_logos) >= 2


def test_orbat_filtering_and_search():
    """Verify branch filtering and text search in ORBAT service."""
    service = OrbatService()

    # Branch filter on Egypt
    naval_units = service.get_orbat_tree(catalog="egypt", branch="Naval")
    assert naval_units.total_units >= 2
    assert all(u.branch == "Naval" for u in naval_units.flat_units)

    # Search filter
    abrams_search = service.get_orbat_tree(catalog="egypt", search="Abrams")
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
        # Default all / egypt
        res = await client.get("/api/orbat")
        assert res.status_code == 200
        data = res.json()
        assert "roots" in data
        assert data["total_units"] >= 10
        assert "catalogs" in data

        # List catalogs endpoint
        res_cat = await client.get("/api/orbat/catalogs")
        assert res_cat.status_code == 200
        cats = res_cat.json()
        assert len(cats) >= 20

        # GeoConfirmed Middle East Catalog
        res_me = await client.get("/api/orbat?catalog=middleeasternfactions")
        assert res_me.status_code == 200
        data_me = res_me.json()
        assert len(data_me["roots"]) >= 1


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
