import random
import string
from datetime import datetime


def generate_order_no() -> str:
    """
    生成随机订单编号：ORD-日期-8位随机字符
    排除易混淆字符：0, O, 1, I
    """
    date_str = datetime.now().strftime("%Y%m%d")
    safe_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_part = "".join(random.choices(safe_chars, k=8))
    return f"ORD-{date_str}-{random_part}"
