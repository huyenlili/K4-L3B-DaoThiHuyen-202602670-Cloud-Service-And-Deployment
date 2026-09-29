# Thông Tin Deploy — Checkpoint 5

## Thông Tin Học Viên

| Mục         | Nội dung                                                   |
| ----------- | ---------------------------------------------------------- |
| Họ và tên   | Đào Thị Huyền                                              |
| Mã học viên | 2A202602670                                                |
| Repo        | https://github.com/huyenlili/K4-L3B-2A20260267-DaoThiHuyen |

## Service

| Mục         | Nội dung                                             |
| ----------- | ---------------------------------------------------- |
| Public URL  | TODO — lấy URL của service `day12-agent` trên Render |
| Platform    | Render                                               |
| Ngày deploy | 29/09/2026                                           |

## Biến Môi Trường Đã Set Trên Cloud

| Biến                    | Đã set | Ghi chú                                          |
| ----------------------- | ------ | ------------------------------------------------ |
| `PORT`                  | ✅      | Platform tự gán                                  |
| `AGENT_API_KEY`         | ✅      | Đặt trong Render Dashboard, không nằm trong repo |
| `REDIS_URL`             | ✅      | Redis service `day12-redis` trên Render          |
| `RATE_LIMIT_PER_MINUTE` | ✅      | 10                                               |
| `MONTHLY_BUDGET_USD`    | ✅      | 10.0                                             |
| `LOG_LEVEL`             | ✅      | INFO                                             |

## Lệnh Kiểm Tra

Thay `<URL>` bằng Public URL của `day12-agent`:

```bash
# 1. Liveness — mong đợi 200 {"status":"ok"}
curl -i <URL>/health

# 2. Readiness — mong đợi 200 {"status":"ready"} và Redis true
curl -i <URL>/ready

# 3. Không có API key — mong đợi 401
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Hello"}'

# 4. Có API key — mong đợi 200 kèm câu trả lời
curl -i -X POST <URL>/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $AGENT_API_KEY" \
  -H "X-User-Id: sv-test" \
  -d '{"question":"Deploy là gì?"}'

# 5. Rate limit — gọi 15 lần
for i in $(seq 1 15); do
  curl -s -o /dev/null -w "%{http_code} " -X POST <URL>/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $AGENT_API_KEY" \
    -H "X-User-Id: sv-test" \
    -d '{"question":"test"}'
done

echo
```

## Kết Quả Chạy Thật

Dán output thực tế của các lệnh trên vào đây:

```text
TODO — chạy các lệnh kiểm tra sau khi lấy Public URL
```

## Ảnh Chụp Màn Hình

Đặt ảnh trong thư mục `screenshots/`:

* `screenshots/dashboard.png` — trang quản lý service `day12-agent` trên Render
* `screenshots/health.png` — kết quả gọi `/health`

---

## Nếu Dùng Phương Án Dự Phòng

Không sử dụng phương án dự phòng vì đã deploy trên Render.
