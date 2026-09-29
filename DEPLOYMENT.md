# Thông Tin Deploy — Checkpoint 5

> Điền file này sau khi deploy xong. `pytest tests/test_cp5.py` đọc file này
> để tìm địa chỉ service của bạn và gọi thử.
>
> **Chỉ ghi TÊN biến môi trường, tuyệt đối không dán giá trị API key vào đây.**
> Repo này công khai — dán khóa vào là mất khóa.

## Thông Tin Học Viên

| Mục | Nội dung |
|-----|----------|
| Họ và tên | Đào Thị Huyền |
| Mã học viên | 2A202602670 |
| Repo | https://github.com/huyenlili/K4-L3B-DaoThiHuyen-202602670-Cloud-Service-And-Deployment.git |

## Service

| Mục | Nội dung |
|-----|----------|
| Public URL | https://day12-agent-g6jh.onrender.com |
| Platform | Render |
| Ngày deploy | 29/09/2026 |
| Trạng thái | Deploy succeeded — Live |
| Thời gian deploy | 46.5 giây |

## Biến Môi Trường Đã Set Trên Cloud

Ghi tên biến và **nguồn giá trị**, không ghi giá trị:

| Biến | Đã set | Ghi chú |
|------|--------|---------|
| `PORT` | ✅ | Platform tự gán |
| `AGENT_API_KEY` | ✅ | Đặt trong Render Dashboard, không nằm trong repo |
| `REDIS_URL` | ✅ | Redis service `day12-redis` trên Render |
| `RATE_LIMIT_PER_MINUTE` | ✅ | 10 |
| `MONTHLY_BUDGET_USD` | ✅ | 10.0 |
| `LOG_LEVEL` | ✅ | INFO |

## Lệnh Kiểm Tra

Public URL: `https://day12-agent-g6jh.onrender.com`

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i https://day12-agent-g6jh.onrender.com/health

# 2. Readiness — mong đợi 200 {"status":"ready"} (đã nối được Redis)
curl -i https://day12-agent-g6jh.onrender.com/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST https://day12-agent-g6jh.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST https://day12-agent-g6jh.onrender.com/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần, những lần cuối phải trả 429
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://day12-agent-g6jh.onrender.com/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done; echo
```

## Kết Quả Chạy Thật
```
# 1. Liveness
HTTP/1.1 200 OK
Date: Tue, 29 Sep 2026 13:19:04 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
cf-cache-status: DYNAMIC
rndr-id: a50467aa-12ac-4cb6
Server: cloudflare
vary: Accept-Encoding
x-render-origin-server: uvicorn
CF-RAY: a42b4679fb282114-HKG
alt-svc: h3=":443"; ma=86400

{"status":"ok","service":"day12-agent","version":"1.0.0"}

# 2. Readiness
HTTP/1.1 200 OK
Date: Tue, 29 Sep 2026 13:20:38 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
cf-cache-status: DYNAMIC
rndr-id: a590538f-f4b1-4a1c
Server: cloudflare
vary: Accept-Encoding
x-render-origin-server: uvicorn
CF-RAY: a42b49508867dd3e-HKG
alt-svc: h3=":443"; ma=86400

{"status":"ready","redis":true}

# 3. Không có API key
HTTP/1.1 401 Unauthorized
Date: Tue, 29 Sep 2026 13:27:51 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
cf-cache-status: DYNAMIC
rndr-id: 7391b975-0c31-4529
Server: cloudflare
vary: Accept-Encoding
x-render-origin-server: uvicorn
CF-RAY: a42b53e009dc0958-HKG
alt-svc: h3=":443"; ma=86400

{"detail":"invalid or missing API key"}

# 4. Có API key
HTTP/1.1 200 OK
Date: Tue, 29 Sep 2026 14:00:47 GMT
Content-Type: application/json
Transfer-Encoding: chunked
Connection: keep-alive
cf-cache-status: DYNAMIC
rndr-id: 1bfa49fb-17ba-49f9
Server: cloudflare
vary: Accept-Encoding
x-render-origin-server: uvicorn
CF-RAY: a42b841eebbe09e0-HKG
alt-svc: h3=":443"; ma=86400

{"answer":"Ngắn gọn: Hello phụ thuộc vào ba yếu tố — cấu hình qua biến môi trường, health check để orchestrator biết trạng thái, và giới hạn tài nguyên.","user_id":"sv-test","history_length":0,"cost_usd":2.115e-05,"tokens":{"in":1,"out":35}}

# 5. Rate limit
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429 
## Ảnh Chụp Màn Hình
```
Đặt ảnh trong thư mục `screenshots/`:

- `screenshots/dashboard.png` — trang quản lý service trên Render
- `screenshots/health.png` — kết quả gọi `/health` từ trình duyệt hoặc curl

