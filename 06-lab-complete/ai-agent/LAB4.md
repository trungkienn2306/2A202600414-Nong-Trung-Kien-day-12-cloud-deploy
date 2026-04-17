# LAB 4: Xây dựng AI Agent đầu tiên với LangGraph

**Thời lượng:** 240 phút (4 giờ)

---

## Bối cảnh

Bối cảnh dự án: startup **TravelBuddy**.

**Nhiệm vụ:** Xây dựng **Trợ lý Du lịch Thông minh** — Agent hỗ trợ người dùng lên kế hoạch chuyến đi bằng cách tự động tìm chuyến bay, kiểm tra ngân sách, và gợi ý khách sạn phù hợp.

**Yêu cầu cốt lõi:** Agent phải **kết hợp** thông tin từ nhiều nguồn để đưa ra gợi ý tối ưu, không chỉ trả lời từng câu hỏi rời rạc.

**Ví dụ:** Khi người dùng nói *"Tôi muốn đi Đà Nẵng cuối tuần này, ngân sách 5 triệu"*, Agent cần tìm chuyến bay, tính phần ngân sách còn lại, và tìm khách sạn phù hợp — **trong một cuộc hội thoại**.

---

## Phần 0: Setup môi trường

**Ước tính:** 30 phút

**Mục tiêu:** Đảm bảo gọi API thành công trước khi làm bài chính.

### 1. Khởi tạo dự án & cài đặt thư viện

```bash
mkdir lab4_agent && cd lab4_agent
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows
pip install langchain langchain-openai langgraph python-dotenv
```

### 2. Cấu hình API Key — tạo file `.env`

Tạo file `.env` với nội dung:

```text
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. Sanity check — tạo file `test_api.py`

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")
print(llm.invoke("Xin chào?").content)
```

**Chạy:** `python test_api.py` — nếu in ra câu trả lời, có thể bắt đầu bài tập.

---

## Phần 1: Thiết kế System Prompt

**Ước tính:** 45 phút

**Mục tiêu:** Định hình *"não bộ"* của Agent — cách nó suy nghĩ và hành xử.

**Nhiệm vụ:** Tạo file `system_prompt.txt` theo cấu trúc XML gồm các phần sau.

### Cấu trúc gợi ý (XML)

**`<persona>`**

> Bạn là trợ lý du lịch của TravelBuddy — thân thiện, am hiểu du lịch Việt Nam, và luôn tư vấn dựa trên ngân sách thực tế của khách hàng. Bạn nói chuyện tự nhiên như một người bạn đi du lịch nhiều, không robot.

**`<rules>`**

1. Trả lời bằng tiếng Việt.
2. *(Sinh viên bổ sung thêm quy tắc cần thiết.)*

**`<tools_instruction>`**

> Bạn có 3 công cụ:

- `search_flights`
- `search_hotels`
- `calculate_budget`

**`<response_format>`**

> Khi tư vấn chuyến đi, trình bày theo cấu trúc:

- **Chuyến bay:** …
- **Khách sạn:** …
- **Tổng chi phí ước tính:** …
- **Gợi ý thêm:** …

**`<constraints>`**

- Từ chối mọi yêu cầu không liên quan đến du lịch/đặt phòng/đặt vé (ví dụ: viết code, làm bài tập, tư vấn tài chính, chính trị).
- *(Sinh viên bổ sung thêm.)*

**Bài tập:** Dựa trên mẫu trên, tùy chỉnh và bổ sung thêm `rules` hoặc `constraints` mà bạn cho là cần thiết. **Giải thích lý do trong comment** (có thể dùng comment XML `<!-- ... -->` nếu muốn giữ file thuần text/XML).

---

## Phần 2: Lập trình Custom Tools

**Ước tính:** 45 phút

**Mục tiêu:** Thiết kế *"tay chân"* cho Agent — 3 tools với mock data có mối liên hệ với nhau.

**Nhiệm vụ:** Tạo file `tools.py`.

### Bắt đầu code `tools.py`

```python
from langchain_core.tools import tool

# MOCK DATA - Dữ liệu giả lập hệ thống du lịch
# Lưu ý: Giá cả có logic (VD: cuối tuần đắt hơn, hạng cao hơn đắt hơn)
# Sinh viên cần đọc hiểu data để debug test cases.

FLIGHTS_DB = {
    ("Hà Nội", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1_450_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2_800_000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1_200_000, "class": "economy"},
    ],
    ("Hà Nội", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1_350_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1_100_000, "class": "economy"},
    ],
    ("Hà Nội", "Hồ Chí Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1_600_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950_000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1_300_000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3_200_000, "class": "business"},
    ],
    ("Hồ Chí Minh", "Đà Nẵng"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1_300_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780_000, "class": "economy"},
    ],
    ("Hồ Chí Minh", "Phú Quốc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1_100_000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650_000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Đà Nẵng": [
        {"name": "Mường Thanh Luxury", "stars": 5, "price_per_night": 1_800_000, "area": "Mỹ Khê", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1_200_000, "area": "Mỹ Khê", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650_000, "area": "Sơn Trà", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250_000, "area": "Hải Châu", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350_000, "area": "An Thượng", "rating": 4.7},
    ],
    "Phú Quốc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3_500_000, "area": "Bãi Dài", "rating": 4.4},
        {"name": "Sol by Meliá", "stars": 4, "price_per_night": 1_500_000, "area": "Bãi Trường", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800_000, "area": "Dương Đông", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200_000, "area": "Dương Đông", "rating": 4.5},
    ],
    "Hồ Chí Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2_800_000, "area": "Quận 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1_400_000, "area": "Quận 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550_000, "area": "Quận 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180_000, "area": "Quận 1", "rating": 4.6},
    ],
}


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Tìm kiếm các chuyến bay giữa hai thành phố.

    Tham số:
    - origin: thành phố khởi hành (VD: 'Hà Nội', 'Hồ Chí Minh')
    - destination: thành phố đến (VD: 'Đà Nẵng', 'Phú Quốc')

    Trả về danh sách chuyến bay với hãng, giờ bay, giá vé.
    Nếu không tìm thấy tuyến bay, trả về thông báo không có chuyến.
    """
    # TODO: Sinh viên tự triển khai
    # - Tra cứu FLIGHTS_DB với key (origin, destination)
    # - Nếu tìm thấy -> format danh sách chuyến bay dễ đọc, bao gồm giá tiền
    # - Nếu không tìm thấy -> thử tra ngược (destination, origin) xem có không,
    #   nếu cũng không có -> "Không tìm thấy chuyến bay từ X đến Y."
    # - Gợi ý: format giá tiền có dấu chấm phân cách (1.450.000đ)
    pass


@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.

    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ), mặc định không giới hạn

    Trả về danh sách khách sạn phù hợp với tên, số sao, giá, khu vực, rating.
    """
    # TODO: Sinh viên tự triển khai
    # - Tra cứu HOTELS_DB[city]
    # - Lọc theo max_price_per_night
    # - Sắp xếp theo rating giảm dần
    # - Format đẹp. Nếu không có kết quả -> "Không tìm thấy khách sạn tại X
    #   với giá dưới Y/đêm. Hãy thử tăng ngân sách."
    pass


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính ngân sách còn lại sau khi trừ các khoản chi.

    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ).
    - expenses: chuỗi mô tả các khoản, mỗi khoản cách nhau bởi dấu phẩy,
      định dạng `tên_khoản:số_tiền`
      (VD: `'vé_máy_bay:890000,khách_sạn:650000'`).

    Trả về bảng chi tiết chi phí và số dư còn lại.
    Nếu vượt ngân sách, cảnh báo rõ số tiền thiếu.
    """
    # TODO: Sinh viên tự triển khai
    # - Parse chuỗi expenses thành dict {tên: số_tiền}
    # - Tính tổng chi phí
    # - Tính số tiền còn lại = total_budget - tổng chi phí
    # - Format bảng chi tiết, ví dụ:
    #   Bảng chi phí:
    #   - Vé máy bay: 890.000đ
    #   - Khách sạn: 650.000đ
    #   ---
    #   Tổng chi: 1.540.000đ
    #   Ngân sách: 5.000.000đ
    #   Còn lại: 3.460.000đ
    # - Nếu âm -> "Vượt ngân sách X đồng! Cần điều chỉnh."
    # - Xử lý lỗi: nếu expenses format sai -> trả về thông báo lỗi rõ ràng
    pass
```

### Kết thúc code `tools.py`

---

### Chú ý

| Tool | Yêu cầu |
|------|--------|
| `search_flights` | Key là **tuple** `(origin, destination)`; thử tra cứu **chiều ngược** nếu không có. |
| `search_hotels` | Phải **lọc** + **sắp xếp**, không chỉ lookup đơn giản. |
| `calculate_budget` | **Parse** chuỗi, **xử lý** sai format, **tính toán** thực tế. |

**Mối liên hệ:** Ba tool **li quan** nhau: kết quả chuyến bay → đưa vào ngân sách → quyết định mức giá khách sạn.

---

## Phần 3: Triển khai LangGraph

**Ước tính:** 60 phút

**Mục tiêu:** Tạo **vòng lặp Agent** — Agent tự quyết định gọi tool nào, bao nhiêu lần.

**Nhiệm vụ:** Tạo file `agent.py`.

### Code `agent.py`

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import search_flights, search_hotels, calculate_budget
from dotenv import load_dotenv

load_dotenv()

# 1. Đọc System Prompt
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 2. Khai báo State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Khởi tạo LLM và Tools
tools_list = [search_flights, search_hotels, calculate_budget]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

# 4. Agent Node
def agent_node(state: AgentState):
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    # === LOGGING ===
    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"Gọi tool: {tc['name']}({tc['args']})")
    else:
        print("Trả lời trực tiếp")

    return {"messages": [response]}

# 5. Xây dựng Graph
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

# TODO: Sinh viên khai báo edges
# builder.add_edge(START, ...)
# builder.add_conditional_edges("agent", tools_condition)
# builder.add_edge("tools", ...)

graph = builder.compile()

# 6. Chat loop
if __name__ == "__main__":
    print("=" * 60)
    print("TravelBuddy - Trợ lý Du lịch Thông minh")
    print("  Gõ 'quit' để thoát")
    print("=" * 60)

    while True:
        user_input = input("\nBạn: ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            break

        print("\nTravelBuddy đang suy nghĩ...")
        result = graph.invoke({"messages": [("human", user_input)]})
        final = result["messages"][-1]
        print(f"\nTravelBuddy: {final.content}")
```

**Gợi ý cho phần TODO edges (sinh viên tự hoàn thiện):**

- Nối `START` → node `agent`.
- Dùng `add_conditional_edges` từ `agent` với `tools_condition` để rẽ sang `tools` hoặc `END`.
- Nối `tools` → quay lại `agent`.

*(Tham khảo tài liệu LangGraph: `ToolNode` + `tools_condition`.)*

### Kết thúc code `agent.py`

---

## Phần 4: Test cases & chẩn đoán

**Ước tính:** 45 phút

Sinh viên chạy agent và nhập **5 kịch bản** sau, chụp hoặc copy kết quả.

### Test 1 — Trả lời trực tiếp (không cần tool)

- **Người dùng:** `Xin chào! Tôi đang muốn đi du lịch nhưng chưa biết đi đâu.`
- **Kỳ vọng:** Agent chào hỏi, hỏi thêm sở thích/ngân sách/thời gian. **Không** gọi tool.

### Test 2 — Một lần gọi tool

- **Người dùng:** `Tìm giúp tôi chuyến bay từ Hà Nội đi Đà Nẵng`
- **Kỳ vọng:** Gọi `search_flights("Hà Nội", "Đà Nẵng")`, liệt kê **4** chuyến bay.

### Test 3 — Chuỗi nhiều bước (multi-step tool chaining)

- **Người dùng:** `Tôi ở Hà Nội, muốn đi Phú Quốc 2 đêm, budget 5 triệu. Tư vấn giúp!`
- **Kỳ vọng:** Agent tự chuỗi:
  1. `search_flights("Hà Nội", "Phú Quốc")` → gợi ý vé rẻ (ví dụ **1.100.000đ**).
  2. `search_hotels("Phú Quốc", max_price phù hợp)` → gợi ý trong tầm giá.
  3. `calculate_budget(5000000, "vé_bay:1100000,khách_sạn:...")` → tính còn lại.
- Sau đó tổng hợp gợi ý đầy đủ kèm bảng chi phí.

### Test 4 — Thiếu thông tin / làm rõ

- **Người dùng:** `Tôi muốn đặt khách sạn`
- **Kỳ vọng:** Agent hỏi lại: thành phố? bao nhiêu đêm? ngân sách? **Không** gọi tool vội.

### Test 5 — Guardrail / từ chối

- **Người dùng:** `Giải giúp tôi bài tập lập trình Python về linked list`
- **Kỳ vọng:** Từ chối lịch sự, nêu rõ chỉ hỗ trợ **du lịch**.

---

## Phần 5: Nộp bài & đánh giá

**Ước tính:** 15 phút

### Nộp bài

Nén thành file **`MSSV_Lab4.zip`** gồm:

| File | Mô tả |
|------|--------|
| `system_prompt.txt` | System prompt đã thiết kế |
| `tools.py` | Triển khai 3 tools |
| `agent.py` | LangGraph + vòng chat |
| `test_results.md` | Copy/paste log console **ít nhất 5** test cases |

### Rubric

| Tiêu chí | Trọng số |
|----------|----------|
| Setup LangGraph đúng (nodes, edges, graph chạy được) | 25% |
| Tool đúng logic + xử lý lỗi (`try`/`except`) | 25% |
| System prompt vững (qua Test 4 + Test 5) | 20% |
| Agent chuỗi multi-step tool thành công (Test 3) | 20% |
| Code sạch, type hints, logging rõ ràng | 10% |

---

*Tài liệu được chuyển từ bài Lab 4 (TravelBuddy / LangGraph). Nếu mock data trong lớp khác một chút so với bản PDF gốc, hãy đối chiếu với slide/giảng viên.*
