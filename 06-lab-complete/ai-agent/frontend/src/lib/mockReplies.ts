function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function randomBetween(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1))
}

const FALLBACK_REPLIES = [
  'Mình gợi ý bạn lên kế hoạch theo 3 lớp: điểm đến → số ngày → ngân sách mỗi ngày. Bạn muốn ưu tiên cái nào trước?',
  'Với chuyến ngắn ngày, nên chọn một “trục” chính (biển, núi, văn hóa) để không bị chạy xô. Bạn thích kiểu nào?',
  'Nhớ dự phòng 10–15% ngân sách cho phát sinh (di chuyển, ăn thêm). Bạn đang đi một mình hay nhóm?',
  'Mùa cao điểm giá chỗ ở thường nhảy — nếu linh hoạt ngày đi, đôi khi tiết kiệm được khá nhiều. Bạn có thể đổi tuần không?',
  'An toàn: lưu bản sao hộ chiếu trên đám mây, ghi địa chỉ ĐSQ/LSQ tại nơi đến. Bạn sắp xuất ngoài hay đi trong nước?',
]

let fallbackIndex = 0

function nextFallback(): string {
  const t = FALLBACK_REPLIES[fallbackIndex % FALLBACK_REPLIES.length]
  fallbackIndex += 1
  return t
}

function normalize(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '')
}

export async function getMockReply(userText: string): Promise<string> {
  await delay(randomBetween(600, 1200))

  const q = normalize(userText.trim())

  if (/(da\s*lat|dalat|đà\s*lạt|lạt\b)/.test(q) || q.includes('da lat')) {
    return 'Đà Lạt hợp đi 3–4 ngày: kết hợp hồ, đồi thông và chợ đêm. Tháng 3–5 thường mát; cuối tuần đông hơn — đặt phòng sớm nếu bạn đi lễ.'
  }
  if (/bien|dao|phu quoc|nha trang|da nang/.test(q)) {
    return 'Chuyến biển nên gói kèm: vé máy bay/xe + chỗ ở gần bãi hoặc trung tâm (tuỳ bạn thích yên hay tiện). Nhớ kem chống nắng và nước uống khi ra nắng lâu.'
  }
  if (/ngan sach|tiet kiem|re|budget/.test(q)) {
    return 'Gợi ý tiết kiệm: ưu tiên phương tiện công cộng, ăn quán địa phương, tránh mua tour gấp tại khách sạn. Bạn có mức “mỗi ngày” khoảng bao nhiêu?'
  }
  if (/bao lau|may ngay|thoi gian|lich trinh/.test(q)) {
    return 'Nếu 2 ngày 1 đêm: 1 ngày “core” điểm chính + nửa ngày thảnh thơi. 4 ngày trở lên có thể thêm 1 điểm phụ trong bán kính 1–2 giờ xe. Bạn có bao nhiêu ngày?'
  }
  if (/ha noi|ho chi minh|sai gon|hue|hoi an|sapa/.test(q)) {
    return 'Thành phố lớn: chia buổi sáng (bảo tàng/chợ) và chiều tối (phố ẩm thực). Đặt vé tham quan online thường rẻ hơn. Bạn muốn nặng văn hóa hay ẩm thực hơn?'
  }
  if (/chao|hello|hi\b|xin chao/.test(q)) {
    return 'Chào bạn! Mình là trợ lý gợi ý du lịch (bản demo). Hỏi mình về điểm đến, lịch trình, ngân sách hoặc mẹo an toàn nhé.'
  }
  if (/cam on|thanks|thank you/.test(q)) {
    return 'Không có chi! Chúc bạn một chuyến đi vui và an toàn. Cần lịch mẫu theo số ngày thì nói mình biết nhé.'
  }

  return nextFallback()
}
