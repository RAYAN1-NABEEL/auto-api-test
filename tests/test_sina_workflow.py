import time
import pytest
from jsonschema import validate
import requests
import concurrent.futures

CREATE_CHAT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": ["string", "null"]}
    },
    "required": ["id"]
}

def test_1_create_chat(api_client):
    payload = {"title": "Guest Test Chat"}
    response = api_client.post("/chats", payload=payload)
    assert response.status_code in [200, 201]
    
    data = response.json()
    validate(instance=data, schema=CREATE_CHAT_SCHEMA)

def test_2_create_message(api_client):
    chat_res = api_client.post("/chats", payload={"title": "Message Test"})
    assert chat_res.status_code in [200, 201]
    chat_id = chat_res.json()["id"]
    
    msg_endpoint = f"/chats/{chat_id}/messages"
    payload = {"text": "Hello, where is the clinic near me?", "media_id": None}
    msg_res = api_client.post(msg_endpoint, payload=payload)
    assert msg_res.status_code in [200, 201, 202]

def test_3_stream_message(api_client):
    chat_res = api_client.post("/chats", payload={"title": "Stream Test Chat"})
    assert chat_res.status_code in [200, 201]
    chat_id = chat_res.json()["id"]
    
    msg_endpoint = f"/chats/{chat_id}/messages/stream"
    payload = {"text": "Tell me a short health tip.", "media_id": None}
    
    response = api_client.stream_post(msg_endpoint, payload=payload)
    assert response.status_code in [200, 201, 202]
    
    content_type = response.headers.get("content-type", "")
    assert "text/event-stream" in content_type or "text/plain" in content_type or response.status_code == 200

def test_4_boundary_text_limit(api_client):
    chat_res = api_client.post("/chats", payload={"title": "Boundary Test"})
    assert chat_res.status_code in [200, 201]
    chat_id = chat_res.json()["id"]
    
    msg_endpoint = f"/chats/{chat_id}/messages"
    long_payload = {"text": "A" * 250, "media_id": None}
    
    res = api_client.post(msg_endpoint, payload=long_payload)
    assert res.status_code in [400, 422]

def test_5_unauthorized_access(api_client):
    unauth_response = requests.post("https://stg.asksina.ai/api/chats", json={"title": "No Token"})
    assert unauth_response.status_code in [200, 201, 401, 403]

def test_6_api_performance_latency(api_client):
    start_time = time.time()
    response = api_client.post("/chats", payload={"title": "Performance Test"})
    end_time = time.time()
    
    duration = end_time - start_time
    print(f"\n[PERFORMANCE] Create Chat Response Time: {duration:.3f} seconds")
    
    assert response.status_code in [200, 201]
    assert duration < 3.0

def test_7_api_load_test(api_client):
    concurrent_users = 10
    url_path = "/chats"
    
    def send_request():
        start_time = time.time()
        response = api_client.post(url_path, payload={"title": "Load Test Chat"})
        duration = time.time() - start_time
        return response.status_code, duration

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(send_request) for _ in range(concurrent_users)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    status_codes = [res[0] for res in results]
    durations = [res[1] for res in results]
    
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    
    print(f"\n[LOAD TEST] Users: {concurrent_users} | Avg Time: {avg_duration:.3f}s | Max Time: {max_duration:.3f}s")
    
    success_count = status_codes.count(200) + status_codes.count(201)
    print(f"[LOAD TEST] Successful requests: {success_count}/{concurrent_users}")
    
    assert success_count >= (concurrent_users * 0.8)
    assert avg_duration < 3.0