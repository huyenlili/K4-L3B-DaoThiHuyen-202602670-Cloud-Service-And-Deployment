# Phiếu Phản Ánh — K4 Level 3B, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn quan sát được khi chạy code.

> **Họ và tên:** Dao Thi Huyen
> **Mã học viên:** 202602670

---

### Câu 1 — Fail fast (CP1)

Một tình huống cụ thể là khi deploy app lên Render nhưng quên cấu hình `AGENT_API_KEY`. Nếu app có giá trị mặc định `"changeme"` thì service vẫn có thể khởi động và tôi có thể tưởng rằng hệ thống đã được cấu hình đúng, trong khi API lại đang dùng một key không an toàn. Với cơ chế fail fast, app dừng ngay khi thiếu biến môi trường bắt buộc, nhờ đó tôi phát hiện lỗi cấu hình ngay lúc khởi động thay vì phát hiện sau khi đã có request thật.

---

### Câu 2 — Log cho máy đọc (CP1)

Một dòng log JSON tôi quan sát được là:

```json
{"event":"service_started","level":"info","timestamp":"2026-09-29T13:55:53.040426+00:00","service":"day12-agent","version":"1.0.0"}
```

Từ log có cấu trúc JSON này, tôi có thể dùng công cụ để lọc theo `event`, `level`, `service` hoặc `timestamp`, và có thể đưa log vào hệ thống log/monitoring để thống kê, tìm kiếm và cảnh báo tự động. Với `print("đã trả lời xong")`, thông tin chỉ là một chuỗi văn bản nên khó phân tích tự động theo từng trường dữ liệu.

---

### Câu 3 — Kích thước image (CP2)

Sau khi build hai phiên bản, tôi ghi số đo thực tế từ lệnh `docker images` vào bảng dưới đây:

| Bản               |                          Dung lượng |
| ----------------- | ----------------------------------: |
| 1 stage (bản đầu) | **[điền số đo thực tế của bạn] MB** |
| Multi-stage       | **[điền số đo thực tế của bạn] MB** |

Phần chênh lệch chủ yếu đến từ các thành phần chỉ cần trong quá trình build nhưng không cần khi chạy production, ví dụ build tools, cache và các dependency hoặc file trung gian phục vụ quá trình cài đặt. Multi-stage giúp chỉ copy những thành phần cần thiết sang image cuối nên image có thể nhỏ hơn.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Khi tôi sửa một ký tự trong `app/main.py` rồi build lại, các layer trước bước `COPY` chứa những file không thay đổi vẫn được Docker lấy từ cache. Layer `COPY` chứa source code thay đổi nên phải chạy lại, và các layer phía sau nó cũng có thể phải build lại.

Nếu đặt `COPY . .` trước `RUN pip install`, chỉ cần thay đổi một file source code cũng có thể làm layer `COPY` thay đổi. Khi đó layer `RUN pip install` phía sau mất cache và phải chạy lại, khiến thời gian build lâu hơn. Vì vậy nên cài dependency trước rồi mới copy source code để tận dụng Docker cache.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Nếu code Python có một lỗ hổng cho phép kẻ tấn công thực thi lệnh trong container, kẻ tấn công có thể lấy được quyền của user đang chạy process. Nếu process chạy bằng `root`, họ có quyền rất cao trong container và có thể tiếp tục khai thác các cấu hình hoặc lỗ hổng khác để tìm cách ảnh hưởng đến host.

Lệnh `USER` chuyển process trong container sang một user không có quyền root. Vì vậy ngay cả khi ứng dụng bị khai thác, quyền của kẻ tấn công bị giới hạn bởi quyền của user đó, làm giảm mức độ ảnh hưởng và cắt giảm một phần chuỗi leo thang đặc quyền.

---

### Câu 6 — Cửa sổ trượt (CP3)

Nếu rate limit là 10 request/phút nhưng dùng cách đếm theo phút đồng hồ và reset ở giây 00, một user có thể gửi tối đa **20 request trong khoảng 2 giây liên tiếp**.

Ví dụ, user gửi 10 request ngay trước thời điểm `12:01:00`, sau đó khi bộ đếm reset lúc `12:01:00` thì gửi thêm 10 request ngay sau đó. Hai nhóm request đều nằm trong khoảng thời gian khoảng 2 giây nhưng thuộc hai phút khác nhau theo cách đếm theo phút đồng hồ.

Sliding window tránh được kiểu vượt giới hạn này vì nó xét các request trong 60 giây gần nhất thay vì chỉ dựa vào ranh giới của phút trên đồng hồ.

---

### Câu 7 — Rate limit và cost guard (CP3)

Rate limit giới hạn **số lượng request** trong một khoảng thời gian, còn cost guard giới hạn **chi phí dự kiến hoặc chi phí đã sử dụng** của user trong tháng.

Ví dụ rate limit có thể cho qua một request nếu user chưa vượt số request/phút, nhưng cost guard vẫn có thể chặn nếu request đó có chi phí dự kiến lớn và tổng chi phí sau request vượt ngân sách tháng.

Ngược lại, một user có thể đã dùng nhiều request nhưng mỗi request có chi phí rất thấp. Khi số request vẫn chưa vượt rate limit thì rate limit cho qua, trong khi cost guard cũng chỉ chặn khi tổng chi phí vượt ngân sách. Vì vậy hai cơ chế kiểm soát hai loại tài nguyên khác nhau: tần suất và tiền.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp `/health` và `/ready` thành một endpoint có kiểm tra Redis, khi Redis mất kết nối trong 30 giây thì container sẽ báo trạng thái không sẵn sàng dù process của app vẫn còn chạy.

Với cụm 3 container, health check sẽ lần lượt nhận trạng thái lỗi hoặc không healthy từ các container. Orchestrator có thể loại các container không healthy khỏi việc nhận traffic hoặc thực hiện restart tùy cấu hình health check. Trong thời gian Redis mất kết nối, cả 3 container có thể cùng bị đánh dấu unhealthy vì chúng cùng phụ thuộc vào Redis. Khi Redis hoạt động lại, các container có thể trở lại trạng thái healthy.

Điểm quan trọng là `/health` chỉ nên kiểm tra process còn sống, còn `/ready` mới phù hợp để kiểm tra app đã sẵn sàng nhận traffic và có đủ dependency cần thiết.

---

### Câu 9 — Stateless (CP4)

Khi chạy:

```bash
docker compose up --scale agent=3
```

và gửi nhiều request với cùng `X-User-Id`, các request có thể được phân phối đến những container khác nhau. Khi lịch sử được lưu trong Redis dùng chung, `history_length` vẫn phản ánh lịch sử chung của user thay vì phụ thuộc vào một container cụ thể.

Nếu lịch sử được lưu trong một `dict` Python trong từng container, mỗi container sẽ có một bản sao bộ nhớ riêng. Khi request chuyển sang container khác, container đó có thể không biết các request trước đó. Vì vậy `history_length` có thể tăng không liên tục, ví dụ một container thấy 1, 2, 3 nhưng khi request chuyển sang container khác lại có thể quay về 1 hoặc một giá trị khác.

Điều này cho thấy state dùng chung nên được lưu ở một hệ thống bên ngoài như Redis để application có thể scale nhiều container mà không phụ thuộc vào bộ nhớ riêng của từng container.

---

### Câu 10 — Deploy thật (CP5)

Một lỗi tôi gặp khi deploy thật là request `POST /ask` trả về lỗi **500 Internal Server Error** dù service trên Render đã báo **Live** và `/health` trả về 200.

Tôi kiểm tra log của Render và tìm thấy traceback:

```text
TypeError: unsupported operand type(s) for +: 'NoneType' and 'float'
```

Lỗi xảy ra trong `CostGuard.check()` tại phép tính `spent_amount + estimated_cost`. Tôi kiểm tra lại hàm `spent()` và phát hiện hàm có gọi Redis `get()` nhưng không trả kết quả về, nên Python mặc định trả `None`.

Tôi sửa hàm để nếu Redis chưa có key thì trả `0.0`, còn nếu có giá trị thì chuyển sang `float`. Sau đó tôi commit và push code để Render deploy lại. Tôi cũng kiểm tra lại `/health` và gọi `/ask` để xác nhận lỗi cũ đã được xử lý.

Sau đó tôi gặp thêm lỗi **422 Unprocessable Entity** khi test `/ask`. Tôi kiểm tra response và thấy nguyên nhân là JSON request bị lỗi format (`JSON decode error`). Tôi chuyển sang tạo `body.json` hợp lệ và gửi bằng `curl.exe --data-binary`, sau đó tiếp tục kiểm tra response.
