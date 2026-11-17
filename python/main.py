from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from arduino.app_bricks.web_ui import WebUI
from arduino.app_peripherals.camera import WebSocketCamera
from arduino.app_utils import App, Bridge

ui = WebUI()
camera = WebSocketCamera(port=8080, resolution=(320, 240), fps=10, secret=None, encrypt=False)
# 降低信心度門檻至 0.35，讓較小或稍微傾斜的物品也能更快被抓到
detection = VideoObjectDetection(camera, confidence=0.35, debounce_sec=0.2)

current_led_text = "READY"

# 忽略常見室內背景物件
IGNORE_LABELS = {
    "person", "chair", "couch", "bed", "dining table",
    "toilet", "sink", "refrigerator", "clock", "vase", "potted plant"
}

# 補齊完整實用的 COCO 垃圾分類規則
TRASH_RULES = {
    # 塑膠回收
    "bottle": ("塑膠回收 (Plastic)", "PLASTIC"),
    "cup": ("塑膠/紙杯 (Cup)", "PLASTIC"),
    "bowl": ("容器回收 (Bowl)", "PLASTIC"),
    "toothbrush": ("塑膠製品 (Plastic)", "PLASTIC"),
    # 紙類回收
    "book": ("紙類回收 (Paper)", "PAPER"),
    # 玻璃回收
    "wine glass": ("玻璃回收 (Glass)", "GLASS"),
    # 電子廢棄物
    "cell phone": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "laptop": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "keyboard": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "mouse": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "remote": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "tv": ("電子廢棄物 (E-Waste)", "EWASTE"),
    "hair drier": ("小型家電 (E-Waste)", "EWASTE"),
    # 廚餘回收
    "banana": ("生廚餘 (Compost)", "COMPOST"),
    "apple": ("生廚餘 (Compost)", "COMPOST"),
    "orange": ("生廚餘 (Compost)", "COMPOST"),
    "broccoli": ("生廚餘 (Compost)", "COMPOST"),
    "carrot": ("生廚餘 (Compost)", "COMPOST"),
    "sandwich": ("熟廚餘 (Food)", "COMPOST"),
    "hot dog": ("熟廚餘 (Food)", "COMPOST"),
    "pizza": ("熟廚餘 (Food)", "COMPOST"),
    "donut": ("熟廚餘 (Food)", "COMPOST"),
    "cake": ("熟廚餘 (Food)", "COMPOST"),
    # 金屬回收
    "spoon": ("金屬餐具 (Metal)", "METAL"),
    "fork": ("金屬餐具 (Metal)", "METAL"),
    "knife": ("金屬餐具 (Metal)", "METAL"),
    "scissors": ("金屬回收 (Metal)", "METAL"),
    # 一般垃圾 / 織物 / 配件
    "backpack": ("一般垃圾/織物 (Trash)", "TRASH"),
    "handbag": ("一般垃圾/織物 (Trash)", "TRASH"),
    "suitcase": ("大型廢棄物 (Trash)", "TRASH"),
    "umbrella": ("一般垃圾 (Trash)", "TRASH"),
    "tie": ("織物類 (Trash)", "TRASH"),
    "sports ball": ("一般垃圾 (Trash)", "TRASH"),
    "teddy bear": ("織物/絨毛 (Trash)", "TRASH"),
}

def get_trash_text() -> str:
    return current_led_text

Bridge.provide("get_trash_text", get_trash_text)

def on_detections(detections: dict) -> None:
    global current_led_text

    # 整理畫面中所有偵測到的物件（包含被忽略的背景物，供診斷面板參考）
    all_detected = []
    for k, v in detections.items():
        if len(v) > 0:
            top_c = max(float(d.get("confidence", 0.0)) for d in v)
            all_detected.append({
                "label": k,
                "confidence": round(top_c * 100, 1),
                "ignored": k in IGNORE_LABELS
            })
    all_detected.sort(key=lambda x: x["confidence"], reverse=True)

    # 過濾掉背景物件後找出最高信心度的目標物
    items = {k: v for k, v in detections.items() if k not in IGNORE_LABELS and len(v) > 0}
    if not items:
        if all_detected:
            ui.send_message("trash_diag", {"candidates": all_detected})
        return

    best_label = max(items.keys(), key=lambda k: max(d.get("confidence", 0.0) for d in items[k]))
    best_conf = max(float(d.get("confidence", 0.0)) for d in items[best_label])
    category_zh, led_word = TRASH_RULES.get(best_label, (f"一般垃圾 ({best_label})", "TRASH"))
    current_led_text = led_word

    ui.send_message(
        "trash_result",
        {
            "item": best_label,
            "confidence": round(best_conf * 100, 1),
            "category": category_zh,
            "led_text": led_word,
            "candidates": all_detected,
        },
    )
    print(f"[AI] {best_label} ({best_conf:.2f}) -> {category_zh} [LED:{led_word}]", flush=True)

detection.on_detect_all(on_detections)
App.run()
