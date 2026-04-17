# KẾT QUẢ CHẠY TEST CHUYÊN ĐỀ LANGGRAPH (LAB 4)

> **Lưu ý:** Script này được chạy tự động để lưu lịch sử console output đẹp vào markdown.

## Test 1 — Trả lời trực tiếp (không cần tool)
**Question:** `Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.`

**Expected behavior:** *Agent chào hỏi, hỏi thêm sở thích/ngân sách/thời gian. Không gọi tool.*

**Question:** `Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 3.20 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Chào bạn! Thật tuyệt khi bạn đang có kế hoạch đi du lịch. Để mình có thể giúp bạn tốt hơn, bạn có thể cho mình biết một số thông tin như:

1. Bạn muốn đi đâu? (Thành phố hoặc địa điểm cụ thể)
2. Thời gian bạn dự định đi là khi nào?
3. Ngân sách của bạn cho chuyến đi này là bao nhiêu?

Mình sẽ giúp bạn tìm kiếm những gợi ý phù hợp nhất!
```

---

## Test 2 — Một lần gọi tool
**Question:** `Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng`

**Expected behavior:** *Gọi search_flights('Hà Nội', 'Đà Nẵng'), liệt kê các chuyến bay.*

**Question:** `Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 1.32 giây

[SYSTEM LOG] GỌI TOOL: search_flights
[SYSTEM LOG] THAM SỐ TRUYỀN VÀO:
{
  "origin": "Hà Nội",
  "destination": "Đà Nẵng"
}

[PROFILER]  Thời gian chờ OpenAI API trả về: 4.61 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Dưới đây là các chuyến bay từ Hà Nội đi Đà Nẵng mà tôi tìm được:

- **Vietnam Airlines**: Khởi hành lúc 06:00 -> Đến lúc 07:20 | Giá: 1.450.000đ | Hạng: economy
- **Vietnam Airlines**: Khởi hành lúc 14:00 -> Đến lúc 15:20 | Giá: 2.800.000đ | Hạng: business
- **VietJet Air**: Khởi hành lúc 08:30 -> Đến lúc 09:50 | Giá: 890.000đ | Hạng: economy
- **Bamboo Airways**: Khởi hành lúc 11:00 -> Đến lúc 12:20 | Giá: 1.200.000đ | Hạng: economy

Bạn có muốn tôi tìm thêm thông tin về khách sạn hoặc có yêu cầu nào khác không? Nếu có ngân sách cụ thể cho chuyến đi này, hãy cho tôi biết để tôi có thể tư vấn tốt hơn nhé!
```

---

## Test 3 — Chuỗi nhiều bước (multi-step tool chaining)
**Question:** `Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!`

**Expected behavior:** *Agent tự chuỗi: search_flights -> search_hotels -> calculate_budget, tổng hợp gợi ý.*

**Question:** `Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 1.33 giây

[SYSTEM LOG] GỌI TOOL: search_flights
[SYSTEM LOG] THAM SỐ TRUYỀN VÀO:
{
  "origin": "Hà Nội",
  "destination": "Phú Quốc"
}

[PROFILER]  Thời gian chờ OpenAI API trả về: 1.44 giây

[SYSTEM LOG] GỌI TOOL: search_hotels
[SYSTEM LOG] THAM SỐ TRUYỀN VÀO:
{
  "city": "Phú Quốc",
  "max_price_per_night": 1900000
}

[PROFILER]  Thời gian chờ OpenAI API trả về: 1.26 giây

[SYSTEM LOG] GỌI TOOL: calculate_budget
[SYSTEM LOG] THAM SỐ TRUYỀN VÀO:
{
  "total_budget": 5000000,
  "expenses": "vé_máy_bay:1350000,khách_sạn:1600000"
}

[PROFILER]  Thời gian chờ OpenAI API trả về: 11.65 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Chào bạn! Dưới đây là gợi ý cho chuyến đi từ Hà Nội đến Phú Quốc trong 2 đêm với ngân sách 5 triệu:

### **Chuyến bay:**
- **VietJet Air**: 
  - Khởi hành: 10:00 -> Đến nơi: 12:15 
  - Giá: **1.350.000đ** (Hạng economy)

### **Khách sạn:**
1. **9Station Hostel** (Khu vực: Dương Đông)
   - Rating: 4.5/5.0
   - Giá: **200.000đ/đêm**
   
2. **Sol by Meliá** (Khu vực: Bãi Trường)
   - Rating: 4.2/5.0
   - Giá: **1.500.000đ/đêm**
   
3. **Lahana Resort** (Khu vực: Dương Đông)
   - Rating: 4.0/5.0
   - Giá: **800.000đ/đêm**

### **Nhật ký chi phí:**
| Khoản chi         | Số tiền      |
|--------------------|--------------|
| Vé máy bay         | 1.350.000đ   |
| Khách sạn (2 đêm)  | 1.600.000đ   |
| **Tổng chi**       | **2.950.000đ** |
| **Ngân sách**      | 5.000.000đ   |
| **Còn lại**        | **2.050.000đ** |

### **Gợi ý thêm:**
Bạn còn dư 2.050.000đ, có thể sử dụng cho các hoạt động vui chơi, ăn uống hoặc mua sắm tại Phú Quốc. Hãy nhớ mang theo kem chống nắng và đồ bơi nhé! Chúc bạn có một chuyến đi tuyệt vời!
```

---

## Test 4 — Thiếu thông tin / làm rõ
**Question:** `Tôi muốn đặt khách sạn`

**Expected behavior:** *Agent hỏi lại: thành phố, số đêm, ngân sách. Không gọi tool vội.*

**Question:** `Tôi muốn đặt khách sạn`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 2.52 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Chào bạn! Để giúp bạn đặt khách sạn, mình cần thêm một số thông tin:

1. Bạn muốn đặt khách sạn ở thành phố nào?
2. Thời gian bạn dự định lưu trú là bao lâu (số đêm)?
3. Ngân sách tối đa cho mỗi đêm là bao nhiêu?

Mong bạn cung cấp thêm thông tin để mình có thể hỗ trợ tốt nhất!
```

---

## Test 5 — Guardrail / từ chối
**Question:** `Giải giúp tôi bài tập lập trình Python về linked list`

**Expected behavior:** *Từ chối lịch sự, nêu rõ chỉ hỗ trợ du lịch.*

**Question:** `Giải giúp tôi bài tập lập trình Python về linked list`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 1.75 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Xin lỗi, nhưng tôi là trợ lý du lịch và không thể giúp bạn với các bài tập lập trình hay vấn đề kỹ thuật. Tuy nhiên, nếu bạn cần tư vấn về chuyến đi, đặt vé máy bay hay khách sạn, tôi rất sẵn lòng hỗ trợ! Bạn có kế hoạch đi đâu không?
```

---

## Test 6 — Xử lý lỗi Timeout khi trả lời quá lâu
**Question:** `[TEST TIMEOUT] Hãy đếm từ 1 đến 10 tỷ.`

**Expected behavior:** *Hệ thống phải ngắt phản hồi quá 45 giây và trả thông báo lỗi hệ thống.*

**Question:** `[TEST TIMEOUT] Hãy đếm từ 1 đến 10 tỷ.`

**System Log (Từ LangGraph Tool Calling):**
```text

```

**Agent Response:**
```text
[LỖI TIMEOUT] Hệ thống tự động ngắt kết nối vì AI xử lý quá lâu (Vượt 45s định mức).
```

---

## Test 7 — Xử lý Memory (k=3)
**Question:** `['Xin chào, tôi tên là Minh Khang.', 'Tôi đang muốn tìm vé máy bay từ Hà Nội đi Đà Nẵng', 'Quên mất, bạn còn nhớ tôi tên là gì và nãy giờ tôi đang tìm điểm đến nào không?']`

**Expected behavior:** *Agent nhớ được tên Minh Khang và đang tìm đi Đà Nẵng (bộ nhớ ConversationBufferWindowMemory k=3).*

**Question:** `Xin chào, tôi tên là Minh Khang.`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 2.15 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Chào anh Minh Khang! Rất vui được gặp anh. Anh đang có kế hoạch du lịch đến đâu và vào thời gian nào? Nếu có ngân sách cụ thể, anh cũng có thể chia sẻ để tôi có thể tư vấn tốt hơn nhé!
```

**Question:** `Tôi đang muốn tìm vé máy bay từ Hà Nội đi Đà Nẵng`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 2.26 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Cảm ơn anh đã cung cấp thông tin! Anh có thể cho tôi biết thời gian dự kiến anh muốn bay từ Hà Nội đến Đà Nẵng không? Ngoài ra, nếu anh có ngân sách cho chuyến bay này, hãy cho tôi biết để tôi có thể tìm kiếm vé phù hợp nhất nhé!
```

**Question:** `Quên mất, bạn còn nhớ tôi tên là gì và nãy giờ tôi đang tìm điểm đến nào không?`

**System Log (Từ LangGraph Tool Calling):**
```text
[PROFILER]  Thời gian chờ OpenAI API trả về: 1.84 giây

[SYSTEM LOG] TRẢ LỜI TRỰC TIẾP KẾT QUẢ TỚI NGƯỜI DÙNG (Không dùng Tool)
```

**Agent Response:**
```text
Dĩ nhiên rồi, anh Minh Khang! Anh đang tìm vé máy bay từ Hà Nội đi Đà Nẵng. Vậy anh có thể cho tôi biết thời gian dự kiến bay và ngân sách cho chuyến bay này không? Điều đó sẽ giúp tôi tìm kiếm vé phù hợp hơn cho anh!
```

---

