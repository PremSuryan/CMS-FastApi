from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


#POST Methd
def test_api():
    res = client.post("/test",json={"name": "Prem"})
    assert res.status_code == 200
    assert res.json()  == {"result": {"name": "Prem"}}


#GET Method
def test_get_api():
    res = client.get("/get_api?name=prem")
    assert res.status_code == 200
    assert res.json() == {"result":"prem"}



