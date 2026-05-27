"""
이커머스 실습 데이터 생성 스크립트

생성 규모:
- customers: 1,000명
- products: 300개
- orders: 20,000건
- order_items: 50,000건
- returns: 1,500건

사용법:
    pip install faker pandas numpy
    python generate_data.py              # 오늘 기준 생성
    python generate_data.py 2026-06-22   # 특정 날짜 기준 생성

출력:
    data/sql/seed_data.sql (기존 테이블 대상 seed INSERT)
"""

import random
import sys
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np
import os

fake = Faker("ko_KR")
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# === 기준일 설정 (실행 시점 or 인자로 지정) ===
if len(sys.argv) > 1:
    TODAY = datetime.strptime(sys.argv[1], "%Y-%m-%d")
else:
    TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# === 설정 ===
NUM_CUSTOMERS = 1000
NUM_PRODUCTS = 300
NUM_ORDERS = 20000
TARGET_ORDER_ITEMS = 50000
NUM_RETURNS = 1500

START_DATE = TODAY - timedelta(days=180)  # 6개월 전
END_DATE = TODAY - timedelta(days=2)  # 이틀 전

CATEGORIES = ["전자기기", "패션", "식품", "생활용품", "뷰티"]
REGIONS = [
    "서울특별시",
    "경기도",
    "인천광역시",
    "부산광역시",
    "대구광역시",
    "광주광역시",
    "대전광역시",
    "울산광역시",
    "세종특별자치시",
    "강원도",
    "충청북도",
    "충청남도",
    "전라북도",
    "전라남도",
    "경상북도",
    "경상남도",
    "제주특별자치도",
]
REGION_WEIGHTS = [25, 20, 8, 7, 5, 4, 4, 3, 1, 3, 3, 3, 3, 3, 3, 3, 2]

GRADE_DISTRIBUTION = {"일반": 0.70, "VIP": 0.25, "VVIP": 0.05}
ORDER_STATUS = ["주문확인", "배송준비", "배송중", "배송완료", "취소"]
RETURN_REASONS = ["단순변심", "불량", "오배송", "사이즈불일치"]
RETURN_REASON_WEIGHTS = [50, 20, 15, 15]
RETURN_STATUS = ["접수", "수거중", "수거완료", "검수완료", "환불완료", "교환발송"]
PAYMENT_METHODS = ["카드", "계좌이체", "포인트", "복합"]
PAYMENT_WEIGHTS = [60, 20, 10, 10]

COUPON_CODES = [None] * 70 + [
    "NEW2024",
    "BIRTH25",
    "BF2024",
    "UPGRADE20",
    "VVIP15",
    "SORRY2K",
]

# === 상품 템플릿 ===
PRODUCT_TEMPLATES = {
    "전자기기": {
        "names": [
            "노트북 Pro {}",
            "무선 이어폰 BT-{}",
            "스마트워치 S{}",
            "태블릿 Tab {}",
            "무선 키보드 K{}",
            "블루투스 스피커 {}",
            "USB 허브 {}포트",
            "무선 마우스 M{}",
            "모니터 {}인치",
            "보조배터리 {}mAh",
            "웹캠 HD {}",
            "외장SSD {}GB",
            "충전기 {}W",
            "케이블 USB-C {}m",
        ],
        "price_range": (15000, 1500000),
    },
    "패션": {
        "names": [
            "캐주얼 자켓 {}",
            "슬림핏 청바지 {}",
            "면 티셔츠 {}",
            "운동화 Runner {}",
            "겨울 패딩 {}",
            "니트 스웨터 {}",
            "정장 셔츠 {}",
            "스니커즈 {}",
            "크로스백 {}",
            "볼캡 {}",
            "머플러 {}",
            "레깅스 {}",
        ],
        "price_range": (15000, 300000),
    },
    "식품": {
        "names": [
            "유기농 과일세트 {}",
            "프리미엄 견과류 {}g",
            "건강즙 {} 팩",
            "단백질 쉐이크 {}",
            "수제 잼 세트 {}",
            "커피 원두 {}g",
            "차 선물세트 {}",
            "건강기능식품 {}",
            "꿀 {}ml",
            "올리브오일 {}ml",
        ],
        "price_range": (10000, 150000),
    },
    "생활용품": {
        "names": [
            "무선 청소기 {}",
            "공기청정기 {}",
            "텀블러 {}ml",
            "수건세트 {}매",
            "식기 세트 {}인용",
            "수납 박스 {}",
            "LED 스탠드 {}",
            "방향제 {}",
            "매트리스 토퍼 {}",
            "이불 세트 {}",
            "실내 슬리퍼 {}",
            "우산 {}",
        ],
        "price_range": (5000, 500000),
    },
    "뷰티": {
        "names": [
            "수분 크림 {}ml",
            "선크림 SPF{}",
            "클렌징 오일 {}ml",
            "세럼 {}ml",
            "립스틱 No.{}",
            "파운데이션 {}",
            "마스크팩 {}매입",
            "향수 {}ml",
            "샴푸 {}ml",
            "바디로션 {}ml",
            "핸드크림 세트 {}",
            "아이크림 {}ml",
        ],
        "price_range": (8000, 200000),
    },
}


def generate_customers():
    """고객 1,000명 생성"""
    customers = []

    # 시나리오용 고객 4명 (ID 고정, 날짜는 상대값)
    scenario_customers = [
        {
            "id": 101,
            "name": "이서연",
            "email": "sy.lee@example.com",
            "phone": "010-3421-7890",
            "grade": "일반",
            "region": "서울특별시",
            "points": 3200,
            "total_spent": 320000,
            "signup_date": TODAY - timedelta(days=120),
        },
        {
            "id": 142,
            "name": "박준혁",
            "email": "jh.park@example.com",
            "phone": "010-5567-1234",
            "grade": "VIP",
            "region": "서울특별시",
            "points": 12500,
            "total_spent": 1250000,
            "signup_date": TODAY - timedelta(days=730),
        },
        {
            "id": 203,
            "name": "김하은",
            "email": "he.kim@example.com",
            "phone": "010-9988-4567",
            "grade": "VVIP",
            "region": "제주특별자치도",
            "points": 45000,
            "total_spent": 5200000,
            "signup_date": TODAY - timedelta(days=960),
        },
        {
            "id": 315,
            "name": "최도윤",
            "email": "dy.choi@example.com",
            "phone": "010-2233-8901",
            "grade": "VIP",
            "region": "경기도",
            "points": 8700,
            "total_spent": 870000,
            "signup_date": TODAY - timedelta(days=450),
        },
    ]
    scenario_ids = {c["id"] for c in scenario_customers}

    # Bulk 고객 생성
    current_id = 1
    for _ in range(NUM_CUSTOMERS - len(scenario_customers)):
        while current_id in scenario_ids:
            current_id += 1

        grade = random.choices(
            list(GRADE_DISTRIBUTION.keys()),
            weights=list(GRADE_DISTRIBUTION.values()),
        )[0]
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]

        if grade == "VVIP":
            total_spent = random.randint(2000000, 10000000)
            points = random.randint(10000, 80000)
        elif grade == "VIP":
            total_spent = random.randint(500000, 2000000)
            points = random.randint(3000, 30000)
        else:
            total_spent = random.randint(0, 500000)
            points = random.randint(0, 10000)

        signup_date = fake.date_between(
            start_date=TODAY - timedelta(days=1095),
            end_date=END_DATE - timedelta(days=30),
        )

        customers.append(
            {
                "id": current_id,
                "name": fake.name(),
                "email": fake.unique.email(),
                "phone": fake.phone_number(),
                "grade": grade,
                "region": region,
                "points": points,
                "total_spent": total_spent,
                "signup_date": signup_date,
            }
        )
        current_id += 1

    customers.extend(scenario_customers)
    customers.sort(key=lambda x: x["id"])
    return customers


def generate_products():
    """상품 300개 생성"""
    products = []
    product_id = 1

    # 시나리오에 필요한 상품 (ID 고정)
    scenario_products = [
        {
            "id": 1001,
            "name": "노트북 Pro 15",
            "category": "전자기기",
            "price": 1290000,
            "stock_status": "판매중",
        },
        {
            "id": 1002,
            "name": "블루투스 이어폰 BT-500",
            "category": "전자기기",
            "price": 89000,
            "stock_status": "판매중",
        },
        {
            "id": 1003,
            "name": "러닝화 Runner X",
            "category": "패션",
            "price": 129000,
            "stock_status": "판매중",
        },
        {
            "id": 1004,
            "name": "캐주얼 자켓 윈터에디션",
            "category": "패션",
            "price": 189000,
            "stock_status": "판매중",
        },
        {
            "id": 1005,
            "name": "무선 키보드 K200",
            "category": "전자기기",
            "price": 59000,
            "stock_status": "판매중",
        },
        {
            "id": 1006,
            "name": "프리미엄 견과류 500g",
            "category": "식품",
            "price": 32000,
            "stock_status": "판매중",
        },
        {
            "id": 1007,
            "name": "수분 크림 50ml",
            "category": "뷰티",
            "price": 45000,
            "stock_status": "판매중",
        },
    ]
    scenario_ids = {p["id"] for p in scenario_products}

    for category, template in PRODUCT_TEMPLATES.items():
        count_per_category = (NUM_PRODUCTS - len(scenario_products)) // len(CATEGORIES)
        for _ in range(count_per_category):
            while product_id in scenario_ids:
                product_id += 1

            name_template = random.choice(template["names"])
            suffix = random.randint(1, 999)
            name = name_template.format(suffix)

            price_min, price_max = template["price_range"]
            price = round(random.randint(price_min, price_max), -2)

            stock_status = random.choices(
                ["판매중", "품절", "단종"], weights=[85, 10, 5]
            )[0]

            products.append(
                {
                    "id": product_id,
                    "name": name,
                    "category": category,
                    "price": price,
                    "stock_status": stock_status,
                }
            )
            product_id += 1

    products.extend(scenario_products)
    products.sort(key=lambda x: x["id"])
    return products


def generate_orders(customers, products):
    """주문 20,000건 + order_items 생성"""
    orders = []
    order_items = []
    order_id = 1
    item_id = 1

    product_ids = [p["id"] for p in products if p["stock_status"] == "판매중"]
    product_prices = {p["id"]: p["price"] for p in products}

    # 등급별 주문 빈도
    grade_order_freq = {"VVIP": 40, "VIP": 25, "일반": 12}

    # 고객별 주문 수 배분
    customer_order_counts = []
    for c in customers:
        base = grade_order_freq[c["grade"]]
        count = max(1, int(np.random.poisson(base)))
        customer_order_counts.append((c["id"], count, c["grade"]))

    # 총 주문 수에 맞게 스케일링
    total_planned = sum(x[1] for x in customer_order_counts)
    scale = NUM_ORDERS / total_planned

    for customer_id, count, grade in customer_order_counts:
        adjusted_count = max(1, int(count * scale))
        for _ in range(adjusted_count):
            if order_id > NUM_ORDERS:
                break

            ordered_at = fake.date_time_between(
                start_date=START_DATE, end_date=END_DATE
            )
            status = random.choices(ORDER_STATUS, weights=[5, 5, 10, 75, 5])[0]

            shipped_at = None
            delivered_at = None
            if status in ("배송중", "배송완료"):
                shipped_at = ordered_at + timedelta(hours=random.randint(6, 48))
            if status == "배송완료":
                delivered_at = shipped_at + timedelta(hours=random.randint(12, 96))

            # 상품 1~5개
            num_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            selected_products = random.sample(
                product_ids, min(num_items, len(product_ids))
            )

            coupon_code = random.choice(COUPON_CODES)
            payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_WEIGHTS)[0]

            order_total = 0
            order_item_list = []
            for pid in selected_products:
                qty = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
                unit_price = product_prices[pid]
                subtotal = unit_price * qty
                order_total += subtotal

                order_item_list.append(
                    {
                        "id": item_id,
                        "order_id": order_id,
                        "product_id": pid,
                        "quantity": qty,
                        "unit_price": unit_price,
                        "subtotal": subtotal,
                        "status": status,
                    }
                )
                item_id += 1

            # 할인 계산
            discount = 0
            if coupon_code == "BF2024":
                discount = min(int(order_total * 0.25), 30000)
            elif coupon_code == "NEW2024":
                discount = min(int(order_total * 0.10), 5000)
            elif coupon_code == "BIRTH25":
                discount = min(int(order_total * 0.15), 10000)
            elif coupon_code == "UPGRADE20":
                discount = min(int(order_total * 0.20), 20000)
            elif coupon_code == "VVIP15":
                discount = min(int(order_total * 0.15), 15000)

            # 묶음배송 할인
            if num_items >= 5:
                discount += int(order_total * 0.10)
            elif num_items >= 3:
                discount += int(order_total * 0.05)

            order_group_id = (
                f"OG-{ordered_at.strftime('%y%m')}-{random.randint(10000, 99999)}"
            )

            orders.append(
                {
                    "id": order_id,
                    "customer_id": customer_id,
                    "order_group_id": order_group_id,
                    "total_amount": order_total - discount,
                    "discount_amount": discount,
                    "coupon_code": coupon_code,
                    "payment_method": payment_method,
                    "status": status,
                    "ordered_at": ordered_at,
                    "shipped_at": shipped_at,
                    "delivered_at": delivered_at,
                }
            )
            order_items.extend(order_item_list)
            order_id += 1

        if order_id > NUM_ORDERS:
            break

    return orders[:NUM_ORDERS], order_items


def generate_returns(orders, order_items):
    """반품 1,500건 생성"""
    returns = []
    return_id = 1

    # 배송완료된 주문에서만 반품 발생
    completed_orders = [o for o in orders if o["status"] == "배송완료"]
    return_candidates = random.sample(
        completed_orders, min(NUM_RETURNS, len(completed_orders))
    )

    for order in return_candidates:
        reason = random.choices(RETURN_REASONS, weights=RETURN_REASON_WEIGHTS)[0]

        # 반품 상태 (시간순으로 진행도 다양하게)
        status_weights = [10, 10, 15, 20, 40, 5]
        status = random.choices(RETURN_STATUS, weights=status_weights)[0]

        requested_at = order["delivered_at"] + timedelta(days=random.randint(0, 6))
        completed_at = None
        if status in ("환불완료", "교환발송"):
            completed_at = requested_at + timedelta(days=random.randint(3, 10))

        refund_amount = None
        if status in ("검수완료", "환불완료"):
            if reason == "단순변심":
                refund_amount = order["total_amount"] - 5000  # 배송비 차감
            else:
                refund_amount = order["total_amount"]  # 전액 환불

        # 해당 주문의 order_item 중 하나 선택
        related_items = [oi for oi in order_items if oi["order_id"] == order["id"]]
        order_item_id = random.choice(related_items)["id"] if related_items else None

        returns.append(
            {
                "id": return_id,
                "order_id": order["id"],
                "order_item_id": order_item_id,
                "reason": reason,
                "status": status,
                "refund_amount": refund_amount,
                "requested_at": requested_at,
                "completed_at": completed_at,
            }
        )
        return_id += 1

    return returns


def insert_scenario_orders(orders, order_items, customers, products):
    """RAG 시나리오용 주문/반품 데이터 삽입"""
    today = TODAY
    max_order_id = max(o["id"] for o in orders)
    max_item_id = max(oi["id"] for oi in order_items)

    scenario_orders = []
    scenario_items = []
    scenario_returns = []

    # 시나리오 1: 고객 142(VIP), 5일 전 노트북 주문, 배송중 (배송 지연)
    oid = max_order_id + 1
    iid = max_item_id + 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 142,
            "order_group_id": f"OG-2505-90001",
            "total_amount": 1290000,
            "discount_amount": 0,
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송중",
            "ordered_at": today - timedelta(days=5),
            "shipped_at": today - timedelta(days=4),
            "delivered_at": None,
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1001,
            "quantity": 1,
            "unit_price": 1290000,
            "subtotal": 1290000,
            "status": "배송중",
        }
    )

    # 시나리오 2: 고객 142(VIP), 블랙프라이데이 쿠폰으로 운동화 구매
    oid += 1
    iid += 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 142,
            "order_group_id": f"OG-2505-90002",
            "total_amount": 99000,
            "discount_amount": 30000,
            "coupon_code": "BF2024",
            "payment_method": "카드",
            "status": "배송완료",
            "ordered_at": today - timedelta(days=8),
            "shipped_at": today - timedelta(days=7),
            "delivered_at": today - timedelta(days=5),
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1003,
            "quantity": 1,
            "unit_price": 129000,
            "subtotal": 129000,
            "status": "배송완료",
        }
    )

    # 시나리오 3: 고객 315(VIP), 블루투스 이어폰 불량 교환
    oid += 1
    iid += 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 315,
            "order_group_id": f"OG-2505-90003",
            "total_amount": 89000,
            "discount_amount": 0,
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송완료",
            "ordered_at": today - timedelta(days=10),
            "shipped_at": today - timedelta(days=9),
            "delivered_at": today - timedelta(days=7),
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1002,
            "quantity": 1,
            "unit_price": 89000,
            "subtotal": 89000,
            "status": "배송완료",
        }
    )
    scenario_returns.append(
        {
            "id": 9001,
            "order_id": oid,
            "order_item_id": iid,
            "reason": "불량",
            "status": "수거완료",
            "refund_amount": None,
            "requested_at": today - timedelta(days=4),
            "completed_at": None,
        }
    )

    # 시나리오 6: 고객 142(VIP), 3개 상품 묶음 주문 (부분 취소 시나리오)
    oid += 1
    iid += 1
    group_id = "OG-2505-90006"
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 142,
            "order_group_id": group_id,
            "total_amount": 177850,
            "discount_amount": 9350,  # 3개 묶음 5% 할인
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송준비",
            "ordered_at": today - timedelta(days=1),
            "shipped_at": None,
            "delivered_at": None,
        }
    )
    # 아이템 3개: 각각 상태 다름
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1005,
            "quantity": 1,
            "unit_price": 59000,
            "subtotal": 59000,
            "status": "주문확인",
        }
    )
    iid += 1
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1006,
            "quantity": 1,
            "unit_price": 32000,
            "subtotal": 32000,
            "status": "배송준비",
        }
    )
    iid += 1
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1007,
            "quantity": 2,
            "unit_price": 45000,
            "subtotal": 90000,
            "status": "배송준비",
        }
    )

    # 시나리오 8: 고객 315(VIP), 오배송
    oid += 1
    iid += 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 315,
            "order_group_id": f"OG-2505-90008",
            "total_amount": 59000,
            "discount_amount": 0,
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송완료",
            "ordered_at": today - timedelta(days=5),
            "shipped_at": today - timedelta(days=4),
            "delivered_at": today - timedelta(days=2),
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1005,
            "quantity": 1,
            "unit_price": 59000,
            "subtotal": 59000,
            "status": "배송완료",
        }
    )
    scenario_returns.append(
        {
            "id": 9002,
            "order_id": oid,
            "order_item_id": iid,
            "reason": "오배송",
            "status": "접수",
            "refund_amount": None,
            "requested_at": today - timedelta(days=1),
            "completed_at": None,
        }
    )

    # 시나리오 9: 고객 315(VIP), 환불 지연 (카드 결제, 검수완료 상태)
    oid += 1
    iid += 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 315,
            "order_group_id": f"OG-2505-90009",
            "total_amount": 45000,
            "discount_amount": 0,
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송완료",
            "ordered_at": today - timedelta(days=15),
            "shipped_at": today - timedelta(days=14),
            "delivered_at": today - timedelta(days=12),
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1007,
            "quantity": 1,
            "unit_price": 45000,
            "subtotal": 45000,
            "status": "배송완료",
        }
    )
    scenario_returns.append(
        {
            "id": 9003,
            "order_id": oid,
            "order_item_id": iid,
            "reason": "단순변심",
            "status": "검수완료",
            "refund_amount": 40000,
            "requested_at": today - timedelta(days=7),
            "completed_at": None,
        }
    )

    # 시나리오 10: 고객 101(일반), 14일 전 자켓 구매 (반품 기한 초과)
    oid += 1
    iid += 1
    scenario_orders.append(
        {
            "id": oid,
            "customer_id": 101,
            "order_group_id": f"OG-2505-90010",
            "total_amount": 189000,
            "discount_amount": 0,
            "coupon_code": None,
            "payment_method": "카드",
            "status": "배송완료",
            "ordered_at": today - timedelta(days=14),
            "shipped_at": today - timedelta(days=13),
            "delivered_at": today - timedelta(days=12),
        }
    )
    scenario_items.append(
        {
            "id": iid,
            "order_id": oid,
            "product_id": 1004,
            "quantity": 1,
            "unit_price": 189000,
            "subtotal": 189000,
            "status": "배송완료",
        }
    )

    return scenario_orders, scenario_items, scenario_returns


def to_sql_value(val):
    """Python 값을 SQL INSERT용 문자열로 변환"""
    if val is None:
        return "NULL"
    elif isinstance(val, str):
        return f"'{val.replace(chr(39), chr(39) + chr(39))}'"
    elif isinstance(val, datetime):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        return f"'{val}'"


SCHEMA_DDL = """\
-- Schema (drop & recreate)
DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(255) NOT NULL UNIQUE,
    phone       VARCHAR(30),
    grade       VARCHAR(20),
    region      VARCHAR(50),
    points      INTEGER NOT NULL DEFAULT 0,
    total_spent BIGINT  NOT NULL DEFAULT 0,
    signup_date DATE
);

CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    category     VARCHAR(50),
    price        INTEGER NOT NULL,
    stock_status VARCHAR(20)
);

CREATE TABLE orders (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    order_group_id  VARCHAR(40),
    total_amount    BIGINT  NOT NULL,
    discount_amount BIGINT  NOT NULL DEFAULT 0,
    coupon_code     VARCHAR(20),
    payment_method  VARCHAR(20),
    status          VARCHAR(20),
    ordered_at      TIMESTAMP,
    shipped_at      TIMESTAMP,
    delivered_at    TIMESTAMP
);

CREATE TABLE order_items (
    id         SERIAL PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity   INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    subtotal   BIGINT  NOT NULL,
    status     VARCHAR(20)
);

CREATE TABLE returns (
    id            SERIAL PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES orders(id),
    order_item_id INTEGER REFERENCES order_items(id),
    reason        VARCHAR(30),
    status        VARCHAR(20),
    refund_amount BIGINT,
    requested_at  TIMESTAMP,
    completed_at  TIMESTAMP
);
"""


def export_sql(customers, products, orders, order_items, returns, output_path):
    """SQL file: schema DDL + batch INSERT + sequence reset"""
    BATCH_SIZE = 500

    def write_batch(f, table, columns, rows, row_formatter):
        f.write(f"\n-- {table} ({len(rows)} rows)\n")
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            f.write(f"INSERT INTO {table} ({columns}) VALUES\n")
            f.write(",\n".join(row_formatter(r) for r in batch))
            f.write(";\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("-- Auto-generated: seed data\n")
        f.write(f"-- Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"-- Base date: {TODAY.strftime('%Y-%m-%d')}\n\n")

        f.write(SCHEMA_DDL)
        f.write("\n")

        write_batch(
            f,
            "customers",
            "id, name, email, phone, grade, region, points, total_spent, signup_date",
            customers,
            lambda c: (
                f"({c['id']}, {to_sql_value(c['name'])}, {to_sql_value(c['email'])}, "
                f"{to_sql_value(c['phone'])}, {to_sql_value(c['grade'])}, {to_sql_value(c['region'])}, "
                f"{c['points']}, {c['total_spent']}, {to_sql_value(c['signup_date'])})"
            ),
        )

        write_batch(
            f,
            "products",
            "id, name, category, price, stock_status",
            products,
            lambda p: (
                f"({p['id']}, {to_sql_value(p['name'])}, {to_sql_value(p['category'])}, "
                f"{p['price']}, {to_sql_value(p['stock_status'])})"
            ),
        )

        write_batch(
            f,
            "orders",
            "id, customer_id, order_group_id, total_amount, discount_amount, "
            "coupon_code, payment_method, status, ordered_at, shipped_at, delivered_at",
            orders,
            lambda o: (
                f"({o['id']}, {o['customer_id']}, {to_sql_value(o['order_group_id'])}, "
                f"{o['total_amount']}, {o['discount_amount']}, {to_sql_value(o['coupon_code'])}, "
                f"{to_sql_value(o['payment_method'])}, {to_sql_value(o['status'])}, "
                f"{to_sql_value(o['ordered_at'])}, {to_sql_value(o['shipped_at'])}, "
                f"{to_sql_value(o['delivered_at'])})"
            ),
        )

        write_batch(
            f,
            "order_items",
            "id, order_id, product_id, quantity, unit_price, subtotal, status",
            order_items,
            lambda oi: (
                f"({oi['id']}, {oi['order_id']}, {oi['product_id']}, "
                f"{oi['quantity']}, {oi['unit_price']}, {oi['subtotal']}, {to_sql_value(oi['status'])})"
            ),
        )

        write_batch(
            f,
            "returns",
            "id, order_id, order_item_id, reason, status, refund_amount, requested_at, completed_at",
            returns,
            lambda r: (
                f"({r['id']}, {r['order_id']}, {to_sql_value(r['order_item_id'])}, "
                f"{to_sql_value(r['reason'])}, {to_sql_value(r['status'])}, "
                f"{to_sql_value(r['refund_amount'])}, {to_sql_value(r['requested_at'])}, "
                f"{to_sql_value(r['completed_at'])})"
            ),
        )

        f.write("\n-- Reset sequences\n")
        f.write(
            f"SELECT setval('customers_id_seq', {max(c['id'] for c in customers)});\n"
        )
        f.write(
            f"SELECT setval('products_id_seq', {max(p['id'] for p in products)});\n"
        )
        f.write(f"SELECT setval('orders_id_seq', {max(o['id'] for o in orders)});\n")
        f.write(
            f"SELECT setval('order_items_id_seq', {max(oi['id'] for oi in order_items)});\n"
        )
        f.write(f"SELECT setval('returns_id_seq', {max(r['id'] for r in returns)});\n")


def main():
    print("=== 이커머스 실습 데이터 생성 시작 ===")
    print(f"기준일: {TODAY.strftime('%Y-%m-%d')}")
    print(
        f"데이터 범위: {START_DATE.strftime('%Y-%m-%d')} ~ {END_DATE.strftime('%Y-%m-%d')}"
    )
    print()

    print("1. 고객 생성 중...")
    customers = generate_customers()
    print(f"   → {len(customers)}명 생성 완료")

    print("2. 상품 생성 중...")
    products = generate_products()
    print(f"   → {len(products)}개 생성 완료")

    print("3. 주문 생성 중...")
    orders, order_items = generate_orders(customers, products)
    print(f"   → 주문 {len(orders)}건, 주문항목 {len(order_items)}건 생성 완료")

    print("4. 반품 생성 중...")
    returns = generate_returns(orders, order_items)
    print(f"   → {len(returns)}건 생성 완료")

    print("5. 시나리오 데이터 삽입 중...")
    scenario_orders, scenario_items, scenario_returns = insert_scenario_orders(
        orders, order_items, customers, products
    )
    orders.extend(scenario_orders)
    order_items.extend(scenario_items)
    returns.extend(scenario_returns)
    print(
        f"   → 시나리오 주문 {len(scenario_orders)}건, 반품 {len(scenario_returns)}건 추가"
    )

    # 출력
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(script_dir, "data", "sql", "seed_data.sql")
    os.makedirs(os.path.dirname(sql_path), exist_ok=True)

    print("6. SQL 파일 출력 중...")
    export_sql(customers, products, orders, order_items, returns, sql_path)
    print(f"   → {sql_path}")

    print("\n=== 생성 완료 ===")
    print(
        f"총 데이터: 고객 {len(customers)}, 상품 {len(products)}, "
        f"주문 {len(orders)}, 주문항목 {len(order_items)}, 반품 {len(returns)}"
    )


if __name__ == "__main__":
    main()
