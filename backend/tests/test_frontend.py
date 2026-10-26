from fastapi.testclient import TestClient

from app import main


def test_serves_frontend_assets_and_client_routes(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text("<div id=\"root\"></div>", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ready')", encoding="utf-8")
    monkeypatch.setattr(main, "FRONTEND_DIR", tmp_path)
    client = TestClient(main.app)

    assert client.get("/").text == "<div id=\"root\"></div>"
    assert client.get("/pipeline").text == "<div id=\"root\"></div>"
    assert client.get("/assets/app.js").text == "console.log('ready')"
    assert client.get("/assets/missing.js").status_code == 404
    assert client.get("/api/unknown").status_code == 404
