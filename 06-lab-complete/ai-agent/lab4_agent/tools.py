from langchain_core.tools import tool

# MOCK DATA - Dữ liệu giả lập hệ thống du lịch
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


def format_vnd_currency(amount: int) -> str:
    """Format tiền tệ sang định dạng của VNĐ, VD: 1.450.000đ"""
    return f"{amount:,}".replace(",", ".") + "đ"

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
    try:
        flights = FLIGHTS_DB.get((origin, destination))
        
        # Nếu không có chuyến bay thẳng, thử tra ngược
        if not flights:
            flights_reverse = FLIGHTS_DB.get((destination, origin))
            if not flights_reverse:
                return f"Không tìm thấy chuyến bay thẳng nào từ {origin} đến {destination}."
            return (f"Không có chuyến bay từ {origin} đi {destination}, "
                    f"nhưng có tuyến ngược lại từ {destination} đi {origin}.")
        
        # Đã tìm thấy
        result_lines = [f"[KẾT QUẢ TÌM CHUYẾN BAY TỪ {origin.upper()} ĐI {destination.upper()}]"]
        for f in flights:
            price_str = format_vnd_currency(f['price'])
            info = f"- {f['airline'].ljust(18)} | Khởi hành: {f['departure']} -> Trực tới: {f['arrival']} | Giá: {price_str} | Hạng: {f['class']}"
            result_lines.append(info)
        return "\n".join(result_lines)
        
    except Exception as e:
        return f"Lỗi hệ thống khi tìm chuyến bay: {str(e)}"


@tool
def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Tìm kiếm khách sạn tại một thành phố, có thể lọc theo giá tối đa mỗi đêm.

    Tham số:
    - city: tên thành phố (VD: 'Đà Nẵng', 'Phú Quốc', 'Hồ Chí Minh')
    - max_price_per_night: giá tối đa mỗi đêm (VNĐ), mặc định không giới hạn

    Trả về danh sách khách sạn phù hợp với tên, số sao, giá, khu vực, rating.
    """
    try:
        hotels = HOTELS_DB.get(city)
        if not hotels:
            return f"Hệ thống chưa có dữ liệu khách sạn tại thành phố {city}."
        
        # Lọc theo budget mỗi đêm
        valid_hotels = [h for h in hotels if h["price_per_night"] <= max_price_per_night]
        
        if not valid_hotels:
            budget_str = format_vnd_currency(max_price_per_night)
            return f"Không tìm thấy khách sạn tại {city} với giá dưới {budget_str}/đêm. Hãy thử tăng ngân sách."
        
        # Sắp xếp theo rating giảm dần
        valid_hotels.sort(key=lambda x: x["rating"], reverse=True)
        
        result_lines = [f"[KẾT QUẢ TÌM KHÁCH SẠN TẠI {city.upper()} TRONG KHOẢNG GIÁ DƯỚI {format_vnd_currency(max_price_per_night)}]"]
        for h in valid_hotels:
            price_str = format_vnd_currency(h['price_per_night'])
            stars_str = f"*" * h['stars']
            info = f"- Khách sạn: {h['name']} {stars_str} | Khu vực: {h['area']} | Rating: {h['rating']}/5.0 | Giá chỉ từ: {price_str}/đêm"
            result_lines.append(info)
        
        return "\n".join(result_lines)

    except Exception as e:
        return f"Lỗi hệ thống khi tìm khách sạn: {str(e)}"


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Tính ngân sách còn lại sau khi trừ các khoản chi.

    Tham số:
    - total_budget: tổng ngân sách ban đầu (VNĐ).
    - expenses: chuỗi mô tả các khoản chi, mỗi khoản cách nhau bởi dấu phẩy,
      định dạng `tên_khoản:số_tiền`
      (VD: `'vé_máy_bay:890000,khách_sạn:650000'`).

    Trả về bảng chi tiết chi phí và số dư còn lại.
    Nếu vượt ngân sách, cảnh báo rõ số tiền thiếu.
    """
    try:
        if not expenses or expenses.strip() == "":
            return "Không cung cấp các khoản chi phí để tính toán."

        items = [x.strip() for x in expenses.split(",") if x.strip()]
        
        total_costs = 0
        details = []
        
        for item in items:
            parts = item.split(":")
            if len(parts) != 2:
                return f"Lỗi format chuỗi expenses. Định dạng bắt buộc là `tên_khoản:số_tiền`. Lỗi tại khoản: '{item}'."
            
            name, str_price = parts
            name = name.strip().replace("_", " ").capitalize()
            try:
                price = int(str_price.strip())
            except ValueError:
                return f"Số tiền không hợp lệ trong mục {name}. Giá trị truyền vào phải là số."
            
            total_costs += price
            details.append(f"- {name}: {format_vnd_currency(price)}")
            
        remaining = total_budget - total_costs
        
        result_lines = ["Bảng chi phí:"]
        result_lines.extend(details)
        result_lines.append("---")
        result_lines.append(f"Tổng chi:  {format_vnd_currency(total_costs)}")
        result_lines.append(f"Ngân sách: {format_vnd_currency(total_budget)}")
        
        if remaining >= 0:
            result_lines.append(f"Còn lại:   {format_vnd_currency(remaining)}")
        else:
            result_lines.append(f"[CẢNH BÁO] Vượt ngân sách {format_vnd_currency(abs(remaining))}! Cần điều chỉnh.")
            
        return "\n".join(result_lines)
    except Exception as e:
        return f"Lỗi trong quá trình tính toán ngân sách: {str(e)}"
