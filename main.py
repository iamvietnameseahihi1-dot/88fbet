import flet as ft
import requests
import time
import threading
import random
from datetime import datetime

# ============================================================
# UTILITY: SAFE MAPPER & FORMAT HELPERS
# ============================================================
_raw_colors = getattr(ft, "colors", None) or getattr(ft, "Colors", None)
_raw_icons = getattr(ft, "icons", None) or getattr(ft, "Icons", None)

class SafeAttrMapper:
    def __init__(self, target_module):
        self._module = target_module

    def __getattr__(self, name):
        if not self._module:
            return name
        if hasattr(self._module, name):
            return getattr(self._module, name)
        
        lower_name = name.lower()
        if hasattr(self._module, lower_name):
            return getattr(self._module, lower_name)
            
        pascal_name = "".join(word.capitalize() for word in name.split("_"))
        if hasattr(self._module, pascal_name):
            return getattr(self._module, pascal_name)
            
        return name

colors = SafeAttrMapper(_raw_colors)
icons = SafeAttrMapper(_raw_icons)

def format_currency(val):
    """Rút gọn định dạng tiền tệ: 50k, 50 Triệu, 1 Tỷ"""
    try:
        val = int(val)
        if abs(val) >= 1_000_000_000:
            v = val / 1_000_000_000
            return f"{v:.2f}".rstrip('0').rstrip('.') + " Tỷ"
        elif abs(val) >= 1_000_000:
            v = val / 1_000_000
            return f"{v:.2f}".rstrip('0').rstrip('.') + " Triệu"
        elif abs(val) >= 1_000:
            v = val / 1_000
            return f"{v:.2f}".rstrip('0').rstrip('.') + "k"
        return f"{val}"
    except:
        return str(val)

def get_alignment_center():
    if hasattr(ft, "alignment") and hasattr(ft.alignment, "center"):
        return ft.alignment.center
    elif hasattr(ft, "Alignment") and hasattr(ft.Alignment, "CENTER"):
        return ft.Alignment.CENTER
    elif hasattr(ft, "Alignment") and hasattr(ft.Alignment, "Center"):
        return ft.Alignment.Center
    return None

def get_margin_only(top=0, bottom=0, left=0, right=0):
    if hasattr(ft, "margin") and hasattr(ft.margin, "only"):
        return ft.margin.only(top=top, bottom=bottom, left=left, right=right)
    elif hasattr(ft, "Margin"):
        return ft.Margin(left, top, right, bottom)
    return None

def get_padding_symmetric(vertical=0, horizontal=0):
    if hasattr(ft, "padding") and hasattr(ft.padding, "symmetric"):
        return ft.padding.symmetric(vertical=vertical, horizontal=horizontal)
    elif hasattr(ft, "Padding") and hasattr(ft.Padding, "symmetric"):
        return ft.Padding.symmetric(vertical=vertical, horizontal=horizontal)
    elif hasattr(ft, "Padding"):
        return ft.Padding(horizontal, vertical, horizontal, vertical)
    return None

def get_main_axis_align(value_str):
    module = getattr(ft, "MainAxisAlignment", None)
    if module:
        return getattr(module, value_str.upper(), getattr(module, value_str.capitalize(), value_str))
    return value_str

def get_cross_axis_align(value_str):
    module = getattr(ft, "CrossAxisAlignment", None)
    if module:
        return getattr(module, value_str.upper(), getattr(module, value_str.capitalize(), value_str))
    return value_str

def get_text_align(value_str):
    module = getattr(ft, "TextAlign", None)
    if module:
        return getattr(module, value_str.upper(), getattr(module, value_str.capitalize(), value_str))
    return value_str

def SafeButton(text, on_click=None, width=None, bgcolor=None, disabled=False):
    btn_cls = getattr(ft, "ElevatedButton", None) or getattr(ft, "FilledButton", None) or getattr(ft, "Button", None)
    kwargs = {"disabled": disabled}
    if on_click: kwargs["on_click"] = on_click
    if width: kwargs["width"] = width
    if bgcolor: kwargs["bgcolor"] = bgcolor
    return btn_cls(text, **kwargs)

def SafeOutlinedButton(text, on_click=None, width=None):
    btn_cls = getattr(ft, "OutlinedButton", None) or getattr(ft, "Button", None)
    kwargs = {}
    if on_click: kwargs["on_click"] = on_click
    if width: kwargs["width"] = width
    return btn_cls(text, **kwargs)

# ============================================================
# LOGIC BLACKJACK & CARD UTILITIES
# ============================================================
SUITS = ['♠', '♣', '♦', '♥']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.id = f"{rank}{suit}"

    def is_red(self):
        return self.suit in ['♦', '♥']

def create_deck():
    deck = [Card(r, s) for r in RANKS for s in SUITS]
    random.shuffle(deck)
    return deck

def calculate_bj_score(cards):
    """Tính điểm Xì Dách / Blackjack chuẩn xác"""
    if not cards:
        return 0, "Chưa có bài"
    
    num_cards = len(cards)
    ranks = [c.rank for c in cards]
    
    if num_cards == 2:
        if ranks.count('A') == 2:
            return 30, "Xì Bàn 👑"
        if 'A' in ranks and any(r in ['10', 'J', 'Q', 'K'] for r in ranks):
            return 22, "Xì Dách 🔥"

    non_ace_sum = sum(10 if r in ['J', 'Q', 'K'] else (1 if r == 'A' else int(r)) for r in cards if r != 'A')
    num_aces = ranks.count('A')
    
    if num_aces == 0:
        score = non_ace_sum
    else:
        possible_scores = []
        def eval_aces(idx, current_sum):
            if idx == num_aces:
                possible_scores.append(current_sum)
                return
            for a_val in [11, 10, 1]:
                eval_aces(idx + 1, current_sum + a_val)
        eval_aces(0, non_ace_sum)
        
        valid_scores = [s for s in possible_scores if s <= 21]
        if valid_scores:
            score = max(valid_scores)
        else:
            score = min(possible_scores)

    if num_cards == 5 and score <= 21:
        return 28, f"Ngũ Linh ({score} điểm) ✨"
        
    if score > 21:
        return score, f"Quắc ({score} điểm) 💥"
    elif score < 16:
        return score, f"Chưa đủ 16 ({score} điểm) ⚠️"
    else:
        return score, f"{score} Điểm"

# ============================================================
# FIREBASE REST API & LEVEL/XP LOGIC
# ============================================================
FIREBASE_PROJECT_ID = "admin88fbet-system"
FIRESTORE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

def calculate_level_info(total_xp):
    """
    Hệ thống cấp độ tối đa 100 cấp theo yêu cầu:
    - 30 cấp đầu: XP yêu cầu giảm 10 lần so với chuẩn gốc (100 * level^2 / 10)
    - 30 cấp tiếp theo (Cấp 31-60): Giống như hiện tại (100 * level^2)
    - 30 cấp kế tiếp (Cấp 61-90): Tăng lên 100 lần (100 * level^2 * 100)
    - 10 cấp cuối (Cấp 91-100): Gấp 1000 lần (100 * level^2 * 1000)
    - Đạt max cấp 100: Giới hạn max, không cộng thêm XP nữa.
    """
    if total_xp < 0:
        total_xp = 0

    level = 1
    accumulated_xp = 0
    
    while level < 100:
        base_needed = 100 * (level ** 2)
        if level <= 30:
            xp_needed = max(1, base_needed // 10)
        elif level <= 60:
            xp_needed = base_needed
        elif level <= 90:
            xp_needed = base_needed * 100
        else:
            xp_needed = base_needed * 1000

        if total_xp < accumulated_xp + xp_needed:
            current_level_xp = total_xp - accumulated_xp
            return level, current_level_xp, xp_needed
        
        accumulated_xp += xp_needed
        level += 1

    # Đã đạt cấp tối đa 100
    max_level_xp = 100 * (100 ** 2) * 1000
    return 100, max_level_xp, max_level_xp

def add_user_xp_and_gold(user_doc_ref, gold_spent, raw_xp_earned):
    """
    Cộng XP và Xu vàng dựa trên quy tắc:
    - Cứ mỗi 1.000 vàng tiêu hao cộng thêm 1 điểm XP.
    - Giới hạn max cấp 100: Đạt giới hạn sẽ không cộng thêm XP nữa.
    """
    current_xp = int(user_doc_ref.get("total_xp", 0))
    current_level, _, _ = calculate_level_info(current_xp)

    # Nếu chưa đạt cấp 100 mới tiếp tục cộng XP
    if current_level < 100:
        xp_from_gold = gold_spent // 1000
        total_xp_to_add = raw_xp_earned + xp_from_gold
        new_total_xp = current_xp + total_xp_to_add
        
        # Đảm bảo không vượt quá mức tối đa của cấp 100 nếu vượt ngưỡng
        max_limit_xp = 0
    else:
        new_total_xp = current_xp

    return new_total_xp

def get_level_badge_and_color(level, role):
    if role == "admin":
        return "👑 ADMIN", colors.PURPLE_ACCENT, colors.PURPLE_400
    if level <= 10:
        return "🥉 Đồng", colors.GREY_400, colors.GREY_600
    elif level <= 30:
        return "🥈 Bạc", colors.GREEN_400, colors.GREEN_700
    elif level <= 50:
        return "🥇 Vàng", colors.BLUE_400, colors.BLUE_700
    elif level <= 70:
        return "💎 Kim Cương", colors.PURPLE_300, colors.PURPLE_600
    elif level <= 90:
        return "🔥 Huyền Thoại", colors.ORANGE_400, colors.RED_600
    elif level < 100:
        return "👑 Hoàng Kim", colors.AMBER_400, colors.AMBER_600
    else:
        return "🐉 Tối Thượng", colors.RED_ACCENT, colors.PINK_600

def get_user_doc(username):
    try:
        res = requests.get(f"{FIRESTORE_URL}/users/{username}", timeout=5)
        if res.status_code == 200:
            fields = res.json().get("fields", {})
            xuvang_val = int(fields.get("xuvang", {}).get("integerValue", 0))
            if xuvang_val == 0 and "vnd" in fields: 
                xuvang_val = int(fields.get("vnd", {}).get("integerValue", 0))

            vnd_val = int(fields.get("balance", {}).get("integerValue", 50000))

            return {
                "username": username,
                "password": fields.get("password", {}).get("stringValue", ""),
                "xuvang": xuvang_val,
                "balance": vnd_val,
                "premix_expires": int(fields.get("premix_expires", {}).get("integerValue", 0)),
                "spremix_expires": int(fields.get("spremix_expires", {}).get("integerValue", 0)),
                "total_xp": int(fields.get("total_xp", {}).get("integerValue", 0)),
                "last_free_spin": int(fields.get("last_free_spin", {}).get("integerValue", 0)),
                "role": fields.get("role", {}).get("stringValue", "user"),
                "is_banned": fields.get("is_banned", {}).get("booleanValue", False),
                "ban_reason": fields.get("ban_reason", {}).get("stringValue", ""),
                "kicked": fields.get("kicked", {}).get("booleanValue", False),
                "kick_reason": fields.get("kick_reason", {}).get("stringValue", "")
            }
    except Exception as e:
        print("Lỗi get_user_doc:", e)
    return None

def update_user_fields(username, update_map):
    fields = {}
    mask = []
    for k, v in update_map.items():
        fields[k] = v
        mask.append(f"updateMask.fieldPaths={k}")
    
    url = f"{FIRESTORE_URL}/users/{username}?" + "&".join(mask)
    try:
        requests.patch(url, json={"fields": fields}, timeout=5)
    except Exception as e:
        print("Lỗi update_user_fields:", e)

def get_system_data():
    try:
        res = requests.get(f"{FIRESTORE_URL}/system/config", timeout=5)
        if res.status_code == 200:
            fields = res.json().get("fields", {})
            return {
                "jackpot_pool": int(fields.get("jackpot_pool", {}).get("integerValue", 10000000)),
                "marquee_message": fields.get("marquee_message", {}).get("stringValue", "Chào mừng bạn đến với Cổng Game!")
            }
    except Exception as e:
        print("Lỗi get_system_data:", e)
    return {"jackpot_pool": 10000000, "marquee_message": "Chào mừng bạn đến với Cổng Game!"}

def update_system_config(update_map):
    fields = {}
    mask = []
    for k, v in update_map.items():
        fields[k] = v
        mask.append(f"updateMask.fieldPaths={k}")
    url = f"{FIRESTORE_URL}/system/config?" + "&".join(mask)
    try:
        requests.patch(url, json={"fields": fields}, timeout=5)
    except Exception as e:
        print("Lỗi update_system_config:", e)

def fetch_all_users_for_leaderboard():
    users = []
    try:
        res = requests.get(f"{FIRESTORE_URL}/users", timeout=5)
        if res.status_code == 200:
            docs = res.json().get("documents", [])
            for doc in docs:
                name_path = doc.get("name", "")
                uname = name_path.split("/")[-1]
                fields = doc.get("fields", {})
                
                raw_xuvang = int(fields.get("xuvang", {}).get("integerValue", 0))
                if raw_xuvang == 0 and "vnd" in fields:
                    raw_xuvang = int(fields.get("vnd", {}).get("integerValue", 0))

                raw_vnd = int(fields.get("balance", {}).get("integerValue", 50000))
                total_xp = int(fields.get("total_xp", {}).get("integerValue", 0))
                role = fields.get("role", {}).get("stringValue", "user")
                
                users.append({
                    "username": uname,
                    "xuvang": raw_xuvang,
                    "balance": raw_vnd,
                    "total_xp": total_xp,
                    "role": role
                })
    except Exception as e:
        print("Lỗi fetch_all_users_for_leaderboard:", e)
    return users

# ============================================================
# MAIN APPLICATION
# ============================================================
def main(page: ft.Page):
    page.title = "Cổng Game Giải Trí Premium"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1100
    page.window.height = 750
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    current_user = None
    is_syncing = False
    current_room_id = None
    in_room_waiting = False

    marquee_text = ft.Text("Đang tải thông báo...", color=colors.YELLOW_300, weight=ft.FontWeight.BOLD)
    marquee_container = ft.Container(
        content=ft.Row([ft.Icon(icons.CAMPAIGN, color=colors.YELLOW_300), marquee_text], alignment=get_main_axis_align("START")),
        bgcolor=colors.GREY_900,
        padding=10,
        border_radius=8,
        margin=get_margin_only(bottom=10)
    )

    kick_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("⚠️ THÔNG BÁO TỪ HỆ THỐNG", color=colors.RED_400, weight=ft.FontWeight.BOLD),
        content=ft.Text(""),
        actions=[SafeButton("Đã hiểu / Đăng nhập lại", on_click=lambda e: close_kick_dialog())],
        actions_alignment=get_main_axis_align("END"),
    )

    def close_kick_dialog():
        kick_dialog.open = False
        page.update()
        show_login_view()

    def trigger_kick_popup(reason):
        kick_dialog.content.value = reason
        if hasattr(page, "open"):
            page.open(kick_dialog)
        else:
            page.dialog = kick_dialog
            kick_dialog.open = True
            page.update()

    def sync_user_status_loop():
        nonlocal current_user, is_syncing
        while is_syncing and current_user:
            time.sleep(5)
            if not is_syncing or not current_user:
                break
            data = get_user_doc(current_user["username"])
            if data:
                if data.get("is_banned"):
                    current_user = None
                    is_syncing = False
                    trigger_kick_popup(f"Tài khoản bị KHÓA!\nLý do: {data.get('ban_reason', 'Không rõ')}")
                    break
                elif data.get("kicked"):
                    update_user_fields(current_user["username"], {"kicked": {"booleanValue": False}, "kick_reason": {"stringValue": ""}})
                    reason = data.get("kick_reason") or "Bạn đã bị kick khỏi hệ thống!"
                    current_user = None
                    is_syncing = False
                    trigger_kick_popup(f"BẠN ĐÃ BỊ KICK KHỎI HỆ THỐNG!\n\nLý do: {reason}")
                    break
            
            sys_d = get_system_data()
            if sys_d:
                marquee_text.value = f"📢 {sys_d['marquee_message']}  |  🔥 HŨ JACKPOT HỆ THỐNG: {sys_d['jackpot_pool']:,} VNĐ"
                page.update()

    def show_toast(msg):
        snack = ft.SnackBar(ft.Text(msg))
        if hasattr(page, "open"):
            page.open(snack)
        else:
            page.snack_bar = snack
            page.snack_bar.open = True
            page.update()

    # ============================================================
    # VIEW: LOGIN & REGISTER
    # ============================================================
    user_input = ft.TextField(label="Tên tài khoản", width=300, icon=icons.PERSON)
    pass_input = ft.TextField(label="Mật khẩu", password=True, can_reveal_password=True, width=300, icon=icons.LOCK)
    status_msg = ft.Text("", color=colors.RED_400)

    def login_click(e):
        nonlocal current_user, is_syncing
        u = user_input.value.strip()
        p = pass_input.value.strip()
        if not u or not p:
            status_msg.value = "Vui lòng nhập đầy đủ thông tin!"
            status_msg.color = colors.RED_400
            page.update()
            return
        
        status_msg.value = "Đang kiểm tra thông tin..."
        status_msg.color = colors.BLUE_300
        page.update()

        user_data = get_user_doc(u)
        if not user_data:
            status_msg.value = "Tài khoản không tồn tại!"
            status_msg.color = colors.RED_400
            page.update()
        elif user_data["password"] != p:
            status_msg.value = "Mật khẩu không chính xác!"
            status_msg.color = colors.RED_400
            page.update()
        elif user_data["is_banned"]:
            trigger_kick_popup(f"Tài khoản đã bị KHÓA!\nLý do: {user_data['ban_reason']}")
        else:
            current_user = user_data
            is_syncing = True
            show_dashboard_view()
            threading.Thread(target=sync_user_status_loop, daemon=True).start()

    def register_click(e):
        u = user_input.value.strip()
        p = pass_input.value.strip()
        if not u or not p:
            status_msg.value = "Vui lòng điền tên & mật khẩu!"
            status_msg.color = colors.RED_400
            page.update()
            return
        
        if get_user_doc(u):
            status_msg.value = "Tài khoản đã tồn tại!"
            status_msg.color = colors.RED_400
        else:
            payload = {
                "fields": {
                    "password": {"stringValue": p},
                    "xuvang": {"integerValue": "50000"},
                    "balance": {"integerValue": "0"},
                    "premix_expires": {"integerValue": "0"},
                    "spremix_expires": {"integerValue": "0"},
                    "total_xp": {"integerValue": "0"},
                    "last_free_spin": {"integerValue": "0"},
                    "role": {"stringValue": "user"},
                    "is_banned": {"booleanValue": False},
                    "ban_reason": {"stringValue": ""},
                    "kicked": {"booleanValue": False},
                    "kick_reason": {"stringValue": ""}
                }
            }
            try:
                res = requests.post(f"{FIRESTORE_URL}/users?documentId={u}", json=payload, timeout=5)
                if res.status_code == 200:
                    status_msg.value = "Đăng ký thành công! Hãy bấm Đăng nhập."
                    status_msg.color = colors.GREEN_400
                else:
                    status_msg.value = "Lỗi đăng ký! Vui lòng thử lại."
                    status_msg.color = colors.RED_400
            except Exception as ex:
                status_msg.value = f"Lỗi kết nối Server: {ex}"
                status_msg.color = colors.RED_400
        page.update()

    def show_login_view():
        nonlocal is_syncing, in_room_waiting
        is_syncing = False
        in_room_waiting = False
        page.clean()
        login_box = ft.Container(
            content=ft.Column([
                ft.Text("🎮 GAMING ENTERTAINMENT", size=26, weight=ft.FontWeight.BOLD, color=colors.BLUE_200),
                ft.Text("Hệ thống Game Giải Trí Premium", size=14, color=colors.GREY_400),
                ft.Divider(height=20, color=colors.TRANSPARENT),
                user_input,
                pass_input,
                status_msg,
                ft.Row([
                    SafeButton("Đăng nhập", on_click=login_click, width=140),
                    SafeOutlinedButton("Đăng ký", on_click=register_click, width=140)
                ], alignment=get_main_axis_align("CENTER"))
            ], horizontal_alignment=get_cross_axis_align("CENTER")),
            padding=40,
            border_radius=15,
            bgcolor=colors.GREY_900,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=colors.BLACK54)
        )
        page.add(ft.Container(content=login_box, alignment=get_alignment_center(), height=600))
        page.update()

    # ============================================================
    # VIEW: BẢNG XẾP HẠNG
    # ============================================================
    def show_leaderboard_view():
        page.clean()
        users_data = fetch_all_users_for_leaderboard()

        list_vnd_view = ft.ListView(expand=True, spacing=6)
        list_gold_view = ft.ListView(expand=True, spacing=6)
        list_level_view = ft.ListView(expand=True, spacing=6)

        user_vnd_rank_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=colors.GREEN_300)
        user_gold_rank_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=colors.AMBER_300)
        user_level_rank_text = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color=colors.PURPLE_300)

        def populate_lists():
            list_vnd_view.controls.clear()
            list_gold_view.controls.clear()
            list_level_view.controls.clear()

            sorted_vnd = sorted(users_data, key=lambda x: x["balance"], reverse=True)
            for i in range(10):
                if i < len(sorted_vnd):
                    u = sorted_vnd[i]
                    rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    list_vnd_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(rank_icon, size=16, weight=ft.FontWeight.BOLD),
                            title=ft.Text(u["username"], color=colors.WHITE, weight=ft.FontWeight.BOLD),
                            trailing=ft.Text(f"{u['balance']:,} VNĐ", color=colors.GREEN_400, weight=ft.FontWeight.BOLD)
                        )
                    )
                else:
                    list_vnd_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(f"#{i+1}", size=16, color=colors.GREY_600),
                            title=ft.Text("--- Trống ---", color=colors.GREY_600),
                            trailing=ft.Text("0 VNĐ", color=colors.GREY_600)
                        )
                    )

            my_vnd_idx = next((idx for idx, item in enumerate(sorted_vnd) if item["username"] == current_user["username"]), None)
            if my_vnd_idx is not None:
                user_vnd_rank_text.value = f"📌 Thứ hạng của bạn: #{my_vnd_idx + 1} ({current_user['balance']:,} VNĐ)"
            else:
                user_vnd_rank_text.value = "📌 Thứ hạng của bạn: Ngoài Top 10"

            sorted_gold = sorted(users_data, key=lambda x: x["xuvang"], reverse=True)
            for i in range(10):
                if i < len(sorted_gold):
                    u = sorted_gold[i]
                    rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    list_gold_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(rank_icon, size=16, weight=ft.FontWeight.BOLD),
                            title=ft.Text(u["username"], color=colors.WHITE, weight=ft.FontWeight.BOLD),
                            trailing=ft.Text(f"{u['xuvang']:,} Xu Vàng", color=colors.AMBER_300, weight=ft.FontWeight.BOLD)
                        )
                    )
                else:
                    list_gold_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(f"#{i+1}", size=16, color=colors.GREY_600),
                            title=ft.Text("--- Trống ---", color=colors.GREY_600),
                            trailing=ft.Text("0 Xu Vàng", color=colors.GREY_600)
                        )
                    )

            my_gold_idx = next((idx for idx, item in enumerate(sorted_gold) if item["username"] == current_user["username"]), None)
            if my_gold_idx is not None:
                user_gold_rank_text.value = f"📌 Thứ hạng của bạn: #{my_gold_idx + 1} ({current_user['xuvang']:,} Xu Vàng)"
            else:
                user_gold_rank_text.value = "📌 Thứ hạng của bạn: Ngoài Top 10"

            sorted_level = sorted(users_data, key=lambda x: x["total_xp"], reverse=True)
            for i in range(10):
                if i < len(sorted_level):
                    u = sorted_level[i]
                    lvl, _, _ = calculate_level_info(u["total_xp"])
                    badge, _, _ = get_level_badge_and_color(lvl, u["role"])
                    rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
                    list_level_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(rank_icon, size=16, weight=ft.FontWeight.BOLD),
                            title=ft.Text(f"{u['username']} ({badge})", color=colors.WHITE, weight=ft.FontWeight.BOLD),
                            trailing=ft.Text(f"Lv.{lvl} ({u['total_xp']} XP)", color=colors.PURPLE_300, weight=ft.FontWeight.BOLD)
                        )
                    )
                else:
                    list_level_view.controls.append(
                        ft.ListTile(
                            leading=ft.Text(f"#{i+1}", size=16, color=colors.GREY_600),
                            title=ft.Text("--- Trống ---", color=colors.GREY_600),
                            trailing=ft.Text("Lv.1 (0 XP)", color=colors.GREY_600)
                        )
                    )

            my_lvl_idx = next((idx for idx, item in enumerate(sorted_level) if item["username"] == current_user["username"]), None)
            my_curr_lvl, _, _ = calculate_level_info(current_user["total_xp"])
            if my_lvl_idx is not None:
                user_level_rank_text.value = f"📌 Thứ hạng của bạn: #{my_lvl_idx + 1} (Lv.{my_curr_lvl} - {current_user['total_xp']} XP)"
            else:
                user_level_rank_text.value = "📌 Thứ hạng của bạn: Ngoài Top 10"

        populate_lists()

        tabs_control = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Top Nạp VNĐ",
                    icon=icons.MONETIZATION_ON,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(content=list_vnd_view, expand=True, bgcolor=colors.GREY_900, border_radius=10, padding=5),
                            ft.Container(content=user_vnd_rank_text, padding=10, bgcolor=colors.GREY_800, border_radius=8, alignment=get_alignment_center())
                        ], expand=True, spacing=10),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Top Xu Vàng Farm",
                    icon=icons.LOCAL_ACTIVITY,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(content=list_gold_view, expand=True, bgcolor=colors.GREY_900, border_radius=10, padding=5),
                            ft.Container(content=user_gold_rank_text, padding=10, bgcolor=colors.GREY_800, border_radius=8, alignment=get_alignment_center())
                        ], expand=True, spacing=10),
                        padding=10
                    )
                ),
                ft.Tab(
                    text="Top Cấp Độ",
                    icon=icons.EMOJI_EVENTS,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Container(content=list_level_view, expand=True, bgcolor=colors.GREY_900, border_radius=10, padding=5),
                            ft.Container(content=user_level_rank_text, padding=10, bgcolor=colors.GREY_800, border_radius=8, alignment=get_alignment_center())
                        ], expand=True, spacing=10),
                        padding=10
                    )
                ),
            ],
            expand=True
        )

        leaderboard_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text("🏆 BẢNG XẾP HẠNG TOP 10", size=20, weight=ft.FontWeight.BOLD, color=colors.AMBER_300)
            ]),
            ft.Divider(height=5),
            ft.Container(content=tabs_control, expand=True)
        ], expand=True, spacing=10)

        page.add(leaderboard_layout)
        page.update()

    # ============================================================
    # VIEW: CỬA HÀNG & NẠP CODE
    # ============================================================
    def show_store_view():
        page.clean()
        nonlocal current_user
        current_user = get_user_doc(current_user["username"])

        store_status_msg = ft.Text("", color=colors.GREEN_400)
        code_input = ft.TextField(label="Nhập mã code (VD: 88fbet-xxxx hoặc premix-xxxx)", width=320)
        
        gift_user_input = ft.TextField(label="Username người nhận", width=200)
        gift_type_dropdown = ft.Dropdown(
            label="Loại quà",
            width=150,
            options=[
                ft.dropdown.Option("balance", "VNĐ (Tiền nạp)"),
                ft.dropdown.Option("xuvang", "Xu Vàng (Chơi game)"),
                ft.dropdown.Option("premix", "Premix"),
                ft.dropdown.Option("spremix", "SPremix"),
            ],
            value="balance"
        )
        gift_amount_input = ft.TextField(label="Số lượng / Số tháng", width=150, keyboard_type=ft.KeyboardType.NUMBER)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ XÁC NHẬN GIAO DỊCH", color=colors.AMBER_300, weight=ft.FontWeight.BOLD),
            content=ft.Text("Bạn có chắc chắn muốn thực hiện giao dịch này?"),
            actions=[],
            actions_alignment=get_main_axis_align("END"),
        )

        def open_confirm_dialog(title_text, content_text, on_confirm_callback):
            confirm_dialog.title = ft.Text(title_text, color=colors.AMBER_300, weight=ft.FontWeight.BOLD)
            confirm_dialog.content = ft.Text(content_text)
            confirm_dialog.actions = [
                SafeButton("Hủy", on_click=lambda e: close_confirm(), bgcolor=colors.GREY_700),
                SafeButton("Xác Nhận", on_click=lambda e: (close_confirm(), on_confirm_callback()), bgcolor=colors.GREEN_700)
            ]
            if hasattr(page, "open"):
                page.open(confirm_dialog)
            else:
                page.dialog = confirm_dialog
                confirm_dialog.open = True
                page.update()

        def close_confirm():
            confirm_dialog.open = False
            page.update()

        def redeem_code_click(e):
            code_str = code_input.value.strip()
            if not code_str:
                store_status_msg.value = "Vui lòng nhập mã code!"
                store_status_msg.color = colors.RED_400
                page.update()
                return

            try:
                res = requests.get(f"{FIRESTORE_URL}/token_codes/{code_str}", timeout=5)
                if res.status_code != 200:
                    store_status_msg.value = "Mã code không tồn tại!"
                    store_status_msg.color = colors.RED_400
                    page.update()
                    return

                doc_json = res.json()
                fields = doc_json.get("fields", {})
                
                is_used = fields.get("used", {}).get("booleanValue", False)
                if is_used:
                    store_status_msg.value = "Mã code này đã được sử dụng trước đó!"
                    store_status_msg.color = colors.RED_400
                    page.update()
                    return

                code_type = fields.get("type", {}).get("stringValue", "").lower()
                
                current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_code_payload = {
                    "fields": {
                        "used": {"booleanValue": True},
                        "used_at": {"stringValue": current_time_str},
                        "used_by": {"stringValue": current_user["username"]}
                    }
                }
                requests.patch(f"{FIRESTORE_URL}/token_codes/{code_str}?updateMask.fieldPaths=used&updateMask.fieldPaths=used_at&updateMask.fieldPaths=used_by", json=update_code_payload, timeout=5)

                if code_type in ["vnd", "nap", "balance", "88fbet", "balance_vnd"]:
                    amount = int(fields.get("amount", {}).get("integerValue", 0))
                    new_vnd = current_user["balance"] + amount
                    update_user_fields(current_user["username"], {"balance": {"integerValue": str(new_vnd)}})
                    current_user["balance"] = new_vnd
                    store_status_msg.value = f"Nạp thành công +{amount:,} VNĐ!"
                elif code_type in ["xuvang", "gold", "vang"]:
                    amount = int(fields.get("amount", {}).get("integerValue", 0))
                    if amount == 0 and "gold_amount" in fields:
                        amount = int(fields.get("gold_amount", {}).get("integerValue", 0))
                        
                    new_xuvang = current_user["xuvang"] + amount
                    update_user_fields(current_user["username"], {"xuvang": {"integerValue": str(new_xuvang)}})
                    current_user["xuvang"] = new_xuvang
                    store_status_msg.value = f"Nhận thành công +{amount:,} Xu Vàng!"
                elif code_type in ["premix", "spremix"]:
                    days = int(fields.get("days", {}).get("integerValue", 30))
                    seconds_duration = days * 24 * 60 * 60
                    curr_time = int(time.time())
                    
                    base_time = max(current_user[f"{code_type}_expires"], curr_time)
                    new_exp = base_time + seconds_duration
                    
                    update_user_fields(current_user["username"], {f"{code_type}_expires": {"integerValue": str(new_exp)}})
                    current_user[f"{code_type}_expires"] = new_exp
                    store_status_msg.value = f"Nạp thành công gói {code_type.upper()} ({days} ngày)!"

                store_status_msg.color = colors.GREEN_400
                code_input.value = ""
                page.update()

            except Exception as ex:
                store_status_msg.value = f"Lỗi hệ thống khi nạp code: {ex}"
                store_status_msg.color = colors.RED_400
                page.update()

        def buy_package(pkg_type, months, price):
            if current_user["balance"] < price:
                store_status_msg.value = f"Không đủ VNĐ! Cần {price:,} VNĐ để mua gói này."
                store_status_msg.color = colors.RED_400
                page.update()
                return

            def execute_buy():
                current_time = int(time.time())
                seconds_per_month = 30 * 24 * 60 * 60
                duration_seconds = months * seconds_per_month

                update_map = {}
                new_vnd = current_user["balance"] - price
                update_map["balance"] = {"integerValue": str(new_vnd)}

                if pkg_type == "premix":
                    base_time = max(current_user["premix_expires"], current_time)
                    new_exp = base_time + duration_seconds
                    update_map["premix_expires"] = {"integerValue": str(new_exp)}
                    current_user["premix_expires"] = new_exp
                elif pkg_type == "spremix":
                    base_time = max(current_user["spremix_expires"], current_time)
                    new_exp = base_time + duration_seconds
                    update_map["spremix_expires"] = {"integerValue": str(new_exp)}
                    current_user["spremix_expires"] = new_exp

                update_user_fields(current_user["username"], update_map)
                current_user["balance"] = new_vnd
                store_status_msg.value = f"Mua thành công gói {pkg_type.upper()} ({months} tháng)!"
                store_status_msg.color = colors.GREEN_400
                page.update()

            open_confirm_dialog(
                "🛒 XÁC NHẬN MUA GÓI VIP",
                f"Bạn có muốn mua gói {pkg_type.upper()} ({months} tháng) với giá {price:,} VNĐ không?",
                execute_buy
            )

        def send_gift_click(e):
            target_name = gift_user_input.value.strip()
            g_type = gift_type_dropdown.value
            try:
                g_val = int(gift_amount_input.value.strip())
            except:
                store_status_msg.value = "Số lượng tặng phải là số nguyên!"
                store_status_msg.color = colors.RED_400
                page.update()
                return

            if not target_name or g_val <= 0:
                store_status_msg.value = "Vui lòng nhập đúng thông tin người nhận và số lượng!"
                store_status_msg.color = colors.RED_400
                page.update()
                return

            if target_name == current_user["username"]:
                store_status_msg.value = "Không thể tự tặng quà cho chính mình!"
                store_status_msg.color = colors.RED_400
                page.update()
                return

            target_data = get_user_doc(target_name)
            if not target_data:
                store_status_msg.value = "Tài khoản người nhận không tồn tại!"
                store_status_msg.color = colors.RED_400
                page.update()
                return

            if g_type == "balance" and current_user["balance"] < g_val:
                store_status_msg.value = "Bạn không đủ VNĐ để tặng!"
                store_status_msg.color = colors.RED_400
                page.update()
                return
            elif g_type == "xuvang" and current_user["xuvang"] < g_val:
                store_status_msg.value = "Bạn không đủ Xu Vàng để tặng!"
                store_status_msg.color = colors.RED_400
                page.update()
                return
            elif g_type in ["premix", "spremix"]:
                price_check = g_val * 100000
                if current_user["balance"] < price_check:
                    store_status_msg.value = f"Không đủ VNĐ để mua gói tặng này (Cần {price_check:,} VNĐ)!"
                    store_status_msg.color = colors.RED_400
                    page.update()
                    return

            def execute_send_gift():
                if g_type == "balance":
                    new_sender_vnd = current_user["balance"] - g_val
                    update_user_fields(current_user["username"], {"balance": {"integerValue": str(new_sender_vnd)}})
                    current_user["balance"] = new_sender_vnd
                    
                    new_target_vnd = target_data["balance"] + g_val
                    update_user_fields(target_name, {"balance": {"integerValue": str(new_target_vnd)}})

                elif g_type == "xuvang":
                    new_sender_gold = current_user["xuvang"] - g_val
                    update_user_fields(current_user["username"], {"xuvang": {"integerValue": str(new_sender_gold)}})
                    current_user["xuvang"] = new_sender_gold
                    
                    new_target_gold = target_data["xuvang"] + g_val
                    update_user_fields(target_name, {"xuvang": {"integerValue": str(new_target_gold)}})

                elif g_type in ["premix", "spremix"]:
                    price_check = g_val * 100000
                    new_sender_vnd = current_user["balance"] - price_check
                    update_user_fields(current_user["username"], {"balance": {"integerValue": str(new_sender_vnd)}})
                    current_user["balance"] = new_sender_vnd

                    curr_time = int(time.time())
                    duration = g_val * 30 * 24 * 60 * 60
                    base_t = max(target_data[f"{g_type}_expires"], curr_time)
                    new_target_exp = base_t + duration
                    update_user_fields(target_name, {f"{g_type}_expires": {"integerValue": str(new_target_exp)}})

                store_status_msg.value = f"Đã tặng thành công cho {target_name}!"
                store_status_msg.color = colors.GREEN_400
                gift_user_input.value = ""
                gift_amount_input.value = ""
                page.update()

            open_confirm_dialog(
                "🎁 XÁC NHẬN TẶNG QUÀ",
                f"Bạn có chắc muốn chuyển {g_val:,} {g_type.upper()} cho tài khoản {target_name} không?",
                execute_send_gift
            )

        def create_package_card(title, pkg_type, months, price, desc):
            return ft.Container(
                content=ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=colors.AMBER_300),
                    ft.Text(f"⏳ {months} Tháng", size=13, color=colors.WHITE),
                    ft.Text(f"💵 Giá: {price:,} VNĐ", size=13, color=colors.GREEN_300, weight=ft.FontWeight.BOLD),
                    ft.Text(desc, size=11, color=colors.GREY_400),
                    SafeButton("Mua Ngay", on_click=lambda e: buy_package(pkg_type, months, price), bgcolor=colors.BLUE_700)
                ], spacing=8),
                padding=15, bgcolor=colors.GREY_900, border_radius=10, width=220
            )

        store_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text("🛒 CỬA HÀNG VIP & NẠP CODE", size=20, weight=ft.FontWeight.BOLD, color=colors.BLUE_200),
                ft.Container(expand=True),
                ft.Text(f"💵 VNĐ: {current_user['balance']:,}đ | 💰 Xu Vàng: {current_user['xuvang']:,}", size=15, color=colors.GREEN_400, weight=ft.FontWeight.BOLD)
            ]),
            ft.Divider(height=10),
            store_status_msg,
            
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("🎟️ NHẬP MÃ CODE HỆ THỐNG", size=14, weight=ft.FontWeight.BOLD, color=colors.YELLOW_300),
                        code_input,
                        SafeButton("Xác Nhận Nạp Code", on_click=redeem_code_click, bgcolor=colors.GREEN_700)
                    ], spacing=10),
                    padding=15, bgcolor=colors.GREY_900, border_radius=10, expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("🎁 TẶNG QUÀ CHO NGƯỜI KHÁC", size=14, weight=ft.FontWeight.BOLD, color=colors.PURPLE_300),
                        ft.Row([gift_user_input, gift_type_dropdown, gift_amount_input], spacing=10),
                        SafeButton("Chuyển Quà", on_click=send_gift_click, bgcolor=colors.PURPLE_700)
                    ], spacing=10),
                    padding=15, bgcolor=colors.GREY_900, border_radius=10, expand=True
                )
            ], alignment=get_main_axis_align("SPACE_BETWEEN")),

            ft.Divider(height=20),
            ft.Text("⭐ MUA GÓI PREMIX (X300% XP & Xu Vàng mini-game)", size=16, weight=ft.FontWeight.BOLD, color=colors.BLUE_300),
            ft.Row([
                create_package_card("Premix 1 Tháng", "premix", 1, 100000, "X300% XP & Xu Vàng"),
                create_package_card("Premix 3 Tháng", "premix", 3, 200000, "X300% XP & Xu Vàng"),
                create_package_card("Premix 6 Tháng", "premix", 6, 300000, "X300% XP & Xu Vàng"),
                create_package_card("Premix 12 Tháng", "premix", 12, 500000, "X300% XP & Xu Vàng"),
            ], wrap=True, spacing=15),

            ft.Divider(height=20),
            ft.Text("🌟 MUA GÓI SPREMIX (Tên Rainbow + 5% Nổ Hũ + Full Premix)", size=16, weight=ft.FontWeight.BOLD, color=colors.PURPLE_300),
            ft.Row([
                create_package_card("SPremix 1 Tháng", "spremix", 1, 200000, "Rainbow + 5% Hũ"),
                create_package_card("SPremix 3 Tháng", "spremix", 3, 400000, "Rainbow + 5% Hũ"),
                create_package_card("SPremix 6 Tháng", "spremix", 6, 600000, "Rainbow + 5% Hũ"),
                create_package_card("SPremix 12 Tháng", "spremix", 12, 800000, "Rainbow + 5% Hũ"),
            ], wrap=True, spacing=15),
        ], expand=True, spacing=15)

        page.add(store_layout)
        page.update()

    # ============================================================
    # VIEW: VÒNG QUAY MAY MẮN
    # ============================================================
    def show_lucky_wheel_view():
        page.clean()
        nonlocal current_user
        current_user = get_user_doc(current_user["username"])
        sys_info = get_system_data()

        wheel_status = ft.Text("Chọn vòng quay bên dưới để thử vận may!", size=15, color=colors.YELLOW_300)
        prize_display = ft.Container(
            content=ft.Text("🎁 CHƯA QUAY THƯỞNG", size=20, weight=ft.FontWeight.BOLD, color=colors.WHITE),
            bgcolor=colors.GREY_800, padding=20, border_radius=12, alignment=get_alignment_center(), width=500
        )
        jackpot_text = ft.Text(f"🔥 Quỹ Hũ Jackpot: {sys_info['jackpot_pool']:,} Xu Vàng", size=16, weight=ft.FontWeight.BOLD, color=colors.AMBER_300)

        def handle_jackpot_win(fee_amount, spin_name):
            sys_d = get_system_data()
            current_jackpot = sys_d["jackpot_pool"]
            won_jackpot_val = int(current_jackpot * 0.3)
            new_jackpot_pool = current_jackpot - won_jackpot_val

            current_user["xuvang"] += won_jackpot_val
            
            # Cân đối XP và Gold (Mỗi 1000 vàng tiêu hao = 1 XP)
            new_total_xp = add_user_xp_and_gold(current_user, fee_amount, 0)
            current_user["total_xp"] = new_total_xp

            update_user_fields(current_user["username"], {
                "xuvang": {"integerValue": str(current_user["xuvang"])},
                "total_xp": {"integerValue": str(new_total_xp)}
            })
            update_system_config({"jackpot_pool": {"integerValue": str(new_jackpot_pool)}})

            announcement = f"🎉 CHÚC MỪNG [{current_user['username']}] ĐÃ NỔ HŨ [{spin_name}] TRỊ GIÁ {won_jackpot_val:,} XU VÀNG!"
            update_system_config({"marquee_message": {"stringValue": announcement}})
            marquee_text.value = f"📢 {announcement}  |  🔥 HŨ JACKPOT: {new_jackpot_pool:,} VNĐ"

            return won_jackpot_val

        def spin_free(e):
            now_t = int(time.time())
            last_spin = current_user.get("last_free_spin", 0)
            elapsed = now_t - last_spin
            cooldown = 3600

            if elapsed < cooldown:
                remaining = cooldown - elapsed
                mins = remaining // 60
                secs = remaining % 60
                wheel_status.value = f"⏳ Vòng quay Free đang hồi chiêu! Vui lòng đợi sau {mins} phút {secs} giây."
                wheel_status.color = colors.RED_400
                page.update()
                return

            current_user["last_free_spin"] = now_t
            update_user_fields(current_user["username"], {"last_free_spin": {"integerValue": str(now_t)}})

            wheel_status.value = "🌀 Đang quay Vòng Quay Free..."
            wheel_status.color = colors.BLUE_300
            page.update()
            time.sleep(1)

            # Đã giảm XP nhận qua mini game theo yêu cầu (ví dụ giảm còn 1/10)
            free_milestones = [5000, 10000, 20000, 30000, 50000, 100000, 200000, 500000]
            free_weights = [4, 4, 4, 4, 4, 10, 20, 50]
            
            is_jackpot = random.random() < 0.005
            if is_jackpot:
                won_val = handle_jackpot_win(0, "Vòng Free")
                prize_display.content.value = f"👑 NỔ HŨ JACKPOT: +{won_val:,} Xu Vàng!"
                wheel_status.value = f"🎉 Chúc mừng bạn đã NỔ HŨ vòng Free thành công!"
            else:
                won_val = random.choices(free_milestones, weights=free_weights, k=1)[0]
                current_user["xuvang"] += won_val
                
                # Thưởng XP giảm xuống nhẹ từ mini game
                raw_xp_reward = 50
                new_total_xp = add_user_xp_and_gold(current_user, 0, raw_xp_reward)
                current_user["total_xp"] = new_total_xp

                update_user_fields(current_user["username"], {
                    "xuvang": {"integerValue": str(current_user["xuvang"])},
                    "total_xp": {"integerValue": str(new_total_xp)}
                })
                prize_display.content.value = f"🎁 TRÚNG: +{won_val:,} Xu Vàng!"
                wheel_status.value = f"Nhận thành công +{won_val:,} Xu Vàng và +{raw_xp_reward} XP từ vòng quay Free!"

            wheel_status.color = colors.GREEN_400
            jackpot_text.value = f"🔥 Quỹ Hũ Jackpot: {get_system_data()['jackpot_pool']:,} Xu Vàng"
            page.update()

        def spin_paid(fee_val, milestones_list, spin_name):
            if current_user["xuvang"] < fee_val:
                wheel_status.value = f"Bạn cần ít nhất {fee_val:,} Xu Vàng để tham gia quay!"
                wheel_status.color = colors.RED_400
                page.update()
                return

            jackpot_contrib = int(fee_val * 0.1)

            sys_d = get_system_data()
            new_pool = sys_d["jackpot_pool"] + jackpot_contrib
            update_system_config({"jackpot_pool": {"integerValue": str(new_pool)}})

            current_user["xuvang"] -= fee_val

            wheel_status.value = f"🌀 Đang quay {spin_name}..."
            wheel_status.color = colors.BLUE_300
            page.update()
            time.sleep(1)

            is_jackpot = random.random() < 0.02
            if is_jackpot:
                won_val = handle_jackpot_win(fee_val, spin_name)
                prize_display.content.value = f"👑 NỔ HŨ JACKPOT: +{won_val:,} Xu Vàng!"
                wheel_status.value = f"🎉 CHÚC MỪNG! BẠN ĐÃ NỔ HŨ {spin_name} THÀNH CÔNG!"
            else:
                low_milestones = milestones_list[:3]
                mid_milestone = [milestones_list[3]]
                high_milestones = milestones_list[4:7]
                special_milestone = [milestones_list[7]]

                rand_choice = random.choices(
                    ["low", "mid", "high", "special"],
                    weights=[50, 30, 15, 5],
                    k=1
                )[0]

                if rand_choice == "low":
                    won_val = random.choice(low_milestones)
                elif rand_choice == "mid":
                    won_val = random.choice(mid_milestone)
                elif rand_choice == "high":
                    won_val = random.choice(high_milestones)
                else:
                    won_val = random.choice(special_milestone)

                current_user["xuvang"] += won_val
                
                # Cứ mỗi 1.000 vàng tiêu hao = 1 điểm XP + XP thưởng mini game (đã hạ thấp)
                raw_xp_reward = 100
                new_total_xp = add_user_xp_and_gold(current_user, fee_val, raw_xp_reward)
                current_user["total_xp"] = new_total_xp

                update_user_fields(current_user["username"], {
                    "xuvang": {"integerValue": str(current_user["xuvang"])},
                    "total_xp": {"integerValue": str(new_total_xp)}
                })
                prize_display.content.value = f"🎁 TRÚNG: +{won_val:,} Xu Vàng!"
                wheel_status.value = f"Nhận thành công +{won_val:,} Xu Vàng và +{raw_xp_reward + (fee_val // 1000)} XP!"

            wheel_status.color = colors.GREEN_400
            jackpot_text.value = f"🔥 Quỹ Hũ Jackpot: {get_system_data()['jackpot_pool']:,} Xu Vàng"
            page.update()

        wheel_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text("🎰 VÒNG QUAY MAY MẮN", size=20, weight=ft.FontWeight.BOLD, color=colors.PURPLE_300),
                ft.Container(expand=True),
                ft.Text(f"💰 Xu Vàng của bạn: {current_user['xuvang']:,}", size=15, color=colors.AMBER_300, weight=ft.FontWeight.BOLD)
            ]),
            ft.Divider(height=10),
            jackpot_text,
            wheel_status,
            prize_display,
            ft.Divider(height=10),
            ft.Text("🌟 LỰA CHỌN VÒNG QUAY:", size=16, weight=ft.FontWeight.BOLD, color=colors.BLUE_300),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Vòng Quay Free", size=15, weight=ft.FontWeight.BOLD, color=colors.GREEN_300),
                        ft.Text("⏳ 1 Lần / 1 Tiếng", size=12, color=colors.GREY_400),
                        ft.Text("🎁 50% trúng 500k Xu", size=12, color=colors.GREY_400),
                        SafeButton("Quay Free", on_click=spin_free, bgcolor=colors.GREEN_700)
                    ], spacing=8),
                    padding=15, bgcolor=colors.GREY_900, border_radius=10, width=240
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Vòng Quay 50.000 Xu", size=15, weight=ft.FontWeight.BOLD, color=colors.AMBER_300),
                        ft.Text("💵 Phí: 50,000 Xu", size=12, color=colors.GREY_400),
                        ft.Text("🎁 5% mốc đặc biệt 5 Triệu", size=12, color=colors.GREY_400),
                        SafeButton("Quay 50k Xu", on_click=lambda e: spin_paid(50000, [0, 10000, 25000, 100000, 500000, 1000000, 2500000, 5000000], "Vòng 50k Xu"), bgcolor=colors.AMBER_800)
                    ], spacing=8),
                    padding=15, bgcolor=colors.GREY_900, border_radius=10, width=240
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Vòng Quay 500.000 Xu", size=15, weight=ft.FontWeight.BOLD, color=colors.PURPLE_300),
                        ft.Text("💵 Phí: 500,000 Xu", size=12, color=colors.GREY_400),
                        ft.Text("🎁 5% mốc đặc biệt 50 Triệu", size=12, color=colors.GREY_400),
                        SafeButton("Quay 500k Xu", on_click=lambda e: spin_paid(500000, [200000, 500000, 1000000, 5000000, 10000000, 20000000, 35000000, 50000000], "Vòng 500k Xu"), bgcolor=colors.PURPLE_700)
                    ], spacing=8),
                    padding=15, bgcolor=colors.GREY_900, border_radius=10, width=240
                ),
            ], wrap=True, spacing=15, alignment=get_main_axis_align("CENTER"))
        ], expand=True, spacing=15)
        page.add(wheel_layout)
        page.update()

    # ============================================================
    # VIEW: RẮN SĂN MỒI
    # ============================================================
    def show_snake_game_view():
        page.clean()
        nonlocal current_user
        current_user = get_user_doc(current_user["username"])

        score_text = ft.Text("Điểm: 0 | Thức ăn đã ăn: 0", size=16, weight=ft.FontWeight.BOLD, color=colors.GREEN_300)
        snake_status = ft.Text("Dùng các nút điều hướng bên dưới để điều khiển Rắn!", size=13, color=colors.GREY_400)

        grid_size = 10
        cells = []
        snake = [(5, 5), (5, 4), (5, 3)]
        food = (random.randint(0, grid_size-1), random.randint(0, grid_size-1))
        direction = "RIGHT"
        score = 0
        game_running = True

        grid_container = ft.GridView(
            expand=False,
            runs_count=grid_size,
            max_extent=40,
            spacing=2,
            run_spacing=2,
            width=420,
            height=420
        )

        def init_grid():
            cells.clear()
            grid_container.controls.clear()
            for r in range(grid_size):
                row_cells = []
                for c in range(grid_size):
                    cell = ft.Container(bgcolor=colors.GREY_800, border_radius=4)
                    row_cells.append(cell)
                    grid_container.controls.append(cell)
                cells.append(row_cells)

        def update_grid_visuals():
            if not game_running: return
            for r in range(grid_size):
                for c in range(grid_size):
                    if (r, c) in snake:
                        cells[r][c].bgcolor = colors.GREEN_500
                    elif (r, c) == food:
                        cells[r][c].bgcolor = colors.RED_500
                    else:
                        cells[r][c].bgcolor = colors.GREY_800
            try:
                page.update()
            except:
                pass

        def game_loop():
            nonlocal snake, food, score, game_running, direction
            while game_running:
                time.sleep(0.4)
                if not game_running: break

                head_r, head_c = snake[0]
                if direction == "UP": head_r -= 1
                elif direction == "DOWN": head_r += 1
                elif direction == "LEFT": head_c -= 1
                elif direction == "RIGHT": head_c += 1

                if head_r < 0 or head_r >= grid_size or head_c < 0 or head_c >= grid_size or (head_r, head_c) in snake:
                    game_running = False
                    now_t = int(time.time())
                    is_vip = (current_user["premix_expires"] > now_t) or (current_user["spremix_expires"] > now_t)
                    mult = 3 if is_vip else 1

                    reward_gold = score * 100 * mult
                    
                    # XP từ mini game đã giảm đi để cân đối với quy tắc tiêu hao
                    raw_reward_xp = score * 5
                    new_total_xp = add_user_xp_and_gold(current_user, 0, raw_reward_xp)

                    current_user["xuvang"] += reward_gold
                    current_user["total_xp"] = new_total_xp
                    
                    update_user_fields(current_user["username"], {
                        "xuvang": {"integerValue": str(current_user["xuvang"])},
                        "total_xp": {"integerValue": str(new_total_xp)}
                    })

                    snake_status.value = f"🎮 Trò chơi kết thúc! Nhận +{reward_gold:,} Xu Vàng và +{raw_reward_xp} XP."
                    snake_status.color = colors.AMBER_300
                    try:
                        page.update()
                    except:
                        pass
                    break

                new_head = (head_r, head_c)
                snake.insert(0, new_head)

                if new_head == food:
                    score += 1
                    score_text.value = f"Điểm: {score * 10} | Thức ăn đã ăn: {score}"
                    food = (random.randint(0, grid_size-1), random.randint(0, grid_size-1))
                else:
                    snake.pop()

                update_grid_visuals()

        def start_game(e):
            nonlocal game_running, snake, food, score, direction
            snake = [(5, 5), (5, 4), (5, 3)]
            food = (random.randint(0, grid_size-1), random.randint(0, grid_size-1))
            direction = "RIGHT"
            score = 0
            game_running = True
            snake_status.value = "🐍 Rắn đang săn mồi..."
            snake_status.color = colors.GREEN_400
            threading.Thread(target=game_loop, daemon=True).start()

        def change_dir(d):
            nonlocal direction
            if (d == "UP" and direction != "DOWN") or \
               (d == "DOWN" and direction != "UP") or \
               (d == "LEFT" and direction != "RIGHT") or \
               (d == "RIGHT" and direction != "LEFT"):
                direction = d

        def go_back(e):
            nonlocal game_running
            game_running = False
            show_dashboard_view()

        init_grid()

        snake_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=go_back),
                ft.Text("🐍 RẮN SĂN MỒI (FARM XU & XP)", size=18, weight=ft.FontWeight.BOLD, color=colors.GREEN_400),
                ft.Container(expand=True),
                score_text
            ]),
            ft.Divider(height=5),
            snake_status,
            ft.Container(content=grid_container, alignment=get_alignment_center(), padding=10),
            ft.Row([
                SafeButton("Bắt Đầu Chơi", on_click=start_game, bgcolor=colors.GREEN_700),
            ], alignment=get_main_axis_align("CENTER")),
            ft.Row([
                SafeButton("⬆️ Lên", on_click=lambda e: change_dir("UP")),
            ], alignment=get_main_axis_align("CENTER")),
            ft.Row([
                SafeButton("⬅️ Trái", on_click=lambda e: change_dir("LEFT")),
                SafeButton("⬇️ Xuống", on_click=lambda e: change_dir("DOWN")),
                SafeButton("➡️ Phải", on_click=lambda e: change_dir("RIGHT")),
            ], alignment=get_main_axis_align("CENTER"))
        ], expand=True, spacing=10)

        page.add(snake_layout)
        page.update()
        update_grid_visuals()

    # ============================================================
    # VIEW: PIKACHU MINI
    # ============================================================
    def show_pikachu_game_view():
        page.clean()
        nonlocal current_user
        current_user = get_user_doc(current_user["username"])

        status_text = ft.Text("Lật các cặp thẻ bài giống nhau để chiến thắng!", size=14, color=colors.AMBER_300)
        
        emojis = ["🍎", "🍌", "🍇", "🍉", "🍓", "🍒", "🍍", "🥝"]
        deck = emojis * 2
        random.shuffle(deck)

        selected_indices = []
        matched_pairs = 0
        card_controls = []

        grid_view = ft.GridView(
            expand=False,
            runs_count=4,
            max_extent=90,
            spacing=8,
            run_spacing=8,
            width=400,
            height=400
        )

        def on_card_click(idx):
            nonlocal selected_indices, matched_pairs
            if idx in selected_indices or card_controls[idx].content.value != "❓":
                return

            card_controls[idx].content.value = deck[idx]
            card_controls[idx].bgcolor = colors.BLUE_800
            page.update()
            selected_indices.append(idx)

            if len(selected_indices) == 2:
                idx1, idx2 = selected_indices
                if deck[idx1] == deck[idx2]:
                    matched_pairs += 1
                    selected_indices.clear()
                    if matched_pairs == len(emojis):
                        now_t = int(time.time())
                        is_vip = (current_user["premix_expires"] > now_t) or (current_user["spremix_expires"] > now_t)
                        mult = 3 if is_vip else 1
                        reward = 2000 * mult

                        raw_xp_reward = 20
                        new_total_xp = add_user_xp_and_gold(current_user, 0, raw_xp_reward)

                        current_user["xuvang"] += reward
                        current_user["total_xp"] = new_total_xp

                        update_user_fields(current_user["username"], {
                            "xuvang": {"integerValue": str(current_user["xuvang"])},
                            "total_xp": {"integerValue": str(new_total_xp)}
                        })
                        status_text.value = f"🎉 Chúc mừng! Thắng +{reward:,} Xu Vàng và +{raw_xp_reward} XP!"
                        status_text.color = colors.GREEN_400
                        page.update()
                else:
                    time.sleep(0.5)
                    card_controls[idx1].content.value = "❓"
                    card_controls[idx1].bgcolor = colors.GREY_800
                    card_controls[idx2].content.value = "❓"
                    card_controls[idx2].bgcolor = colors.GREY_800
                    selected_indices.clear()
                    page.update()

        for i in range(len(deck)):
            btn = ft.Container(
                content=ft.Text("❓", size=24),
                bgcolor=colors.GREY_800,
                alignment=get_alignment_center(),
                border_radius=8,
                on_click=lambda e, idx=i: on_card_click(idx),
                ink=True
            )
            card_controls.append(btn)
            grid_view.controls.append(btn)

        pikachu_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text("🧩 PIKACHU MINI - GHÉP CẶP", size=18, weight=ft.FontWeight.BOLD, color=colors.AMBER_300)
            ]),
            ft.Divider(height=5),
            status_text,
            ft.Container(content=grid_view, alignment=get_alignment_center(), padding=10)
        ], expand=True, spacing=10)

        page.add(pikachu_layout)
        page.update()

    # ============================================================
    # VIEW: GAME SLOT PENTA SEVEN 5x5
    # ============================================================
    def show_penta_seven_slot_view():
        page.clean()
        nonlocal current_user
        current_user = get_user_doc(current_user["username"])

        sys_d = get_system_data()
        jackpot_pool = sys_d["jackpot_pool"]

        bet_dropdown_slot = ft.Dropdown(
            label="Mức Cược / Lượt",
            width=180,
            options=[
                ft.dropdown.Option("50000", "50k Xu"),
                ft.dropdown.Option("100000", "100k Xu"),
                ft.dropdown.Option("500000", "500k Xu"),
                ft.dropdown.Option("5000000", "5 Triệu Xu"),
                ft.dropdown.Option("10000000", "10 Triệu Xu"),
                ft.dropdown.Option("50000000", "50 Triệu Xu"),
                ft.dropdown.Option("100000000", "100 Triệu Xu"),
            ],
            value="50000"
        )

        spins_count_dropdown = ft.Dropdown(
            label="Số lượt quay",
            width=140,
            options=[
                ft.dropdown.Option("1", "1 Lượt"),
                ft.dropdown.Option("5", "5 Lượt"),
                ft.dropdown.Option("10", "10 Lượt"),
                ft.dropdown.Option("20", "20 Lượt"),
                ft.dropdown.Option("50", "50 Lượt"),
                ft.dropdown.Option("100", "100 Lượt"),
            ],
            value="1"
        )

        jackpot_text = ft.Text(f"🔥 QUỸ HŨ JACKPOT: {format_currency(jackpot_pool)} Xu Vàng", size=18, weight=ft.FontWeight.BOLD, color=colors.AMBER_300)
        slot_status = ft.Text("Tỷ lệ quay chuẩn Slot Game: 50% Trắng | 20% Lỗ ít | 30% Lời", size=14, color=colors.GREY_300)
        win_display = ft.Text("Thắng: 0 Xu", size=18, weight=ft.FontWeight.BOLD, color=colors.GREEN_400)

        symbols_list = ["7️⃣", "💎", "👑", "🍒", "🔔", "🍋", "🍇"]
        grid_cells = []
        grid_container = ft.GridView(runs_count=5, max_extent=70, spacing=6, run_spacing=6, width=380, height=380)

        for _ in range(25):
            c = ft.Container(
                content=ft.Text("❓", size=28),
                bgcolor=colors.GREY_800,
                alignment=get_alignment_center(),
                border_radius=8,
                border=ft.border.all(1, colors.GREY_700)
            )
            grid_cells.append(c)
            grid_container.controls.append(c)

        def spin_slot(e):
            nonlocal jackpot_pool
            bet_val = int(bet_dropdown_slot.value)
            num_spins = int(spins_count_dropdown.value)
            total_cost = bet_val * num_spins

            if current_user["xuvang"] < total_cost:
                slot_status.value = f"Không đủ Xu Vàng! Cần tối thiểu {format_currency(total_cost)} Xu cho {num_spins} lượt."
                slot_status.color = colors.RED_400
                page.update()
                return

            slot_status.value = f"🌀 Đang xử lý {num_spins} lượt quay..."
            slot_status.color = colors.BLUE_300
            page.update()

            total_win_all_spins = 0
            jackpot_hit_count = 0
            last_matrix = None

            for _ in range(num_spins):
                current_user["xuvang"] -= bet_val
                jackpot_contrib = int(bet_val * 0.05)
                jackpot_pool += jackpot_contrib

                matrix = []
                count_8 = 0
                for r in range(5):
                    row = []
                    for c in range(5):
                        if random.random() < 0.005:
                            s = "8️⃣"
                            count_8 += 1
                        else:
                            s = random.choice(symbols_list)
                        row.append(s)
                    matrix.append(row)

                tier_outcome = random.choices(["TRANG", "LO", "LOI"], weights=[50, 20, 30], k=1)[0]
                spin_win = 0

                if tier_outcome == "TRANG":
                    spin_win = 0
                elif tier_outcome == "LO":
                    pct = random.choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
                    spin_win = int(bet_val * pct)
                else:
                    m_mult = random.uniform(1.2, 5.0)
                    spin_win = int(bet_val * m_mult)

                    if random.random() < 0.03:
                        jackpot_won = jackpot_pool
                        jackpot_pool = 300000000
                        spin_win += jackpot_won
                        jackpot_hit_count += 1
                        msg_ann = f"🎉 CHÚC MỪNG [{current_user['username']}] NỔ HŨ PENTA SEVEN NHẬN {format_currency(jackpot_won)} XU!"
                        update_system_config({"marquee_message": {"stringValue": msg_ann}})

                if count_8 > 0 and spin_win > 0:
                    spin_win = int(spin_win * (2 * count_8))

                if spin_win > 0:
                    current_user["xuvang"] += spin_win
                    total_win_all_spins += spin_win

                last_matrix = matrix

            # Cộng XP dựa trên tổng số vàng tiêu hao qua các lượt quay slot (1000 vàng tiêu hao = 1 XP)
            new_total_xp = add_user_xp_and_gold(current_user, total_cost, 0)
            current_user["total_xp"] = new_total_xp

            update_system_config({"jackpot_pool": {"integerValue": str(jackpot_pool)}})
            update_user_fields(current_user["username"], {
                "xuvang": {"integerValue": str(current_user["xuvang"])},
                "total_xp": {"integerValue": str(new_total_xp)}
            })

            idx = 0
            for r in range(5):
                for c in range(5):
                    grid_cells[idx].content.value = last_matrix[r][c]
                    grid_cells[idx].bgcolor = colors.AMBER_900 if last_matrix[r][c] == "8️⃣" else colors.GREY_800
                    idx += 1

            net_profit = total_win_all_spins - total_cost
            profit_str = f"+{format_currency(net_profit)}" if net_profit >= 0 else f"{format_currency(net_profit)}"
            
            win_display.value = f"Tổng thắng {num_spins} lượt: +{format_currency(total_win_all_spins)} Xu (Lời/Lỗ: {profit_str})"
            
            status_msg = f"Đã hoàn thành {num_spins} lượt quay! (+{total_cost // 1000} XP từ tiêu hao vàng)"
            if jackpot_hit_count > 0:
                status_msg += f" 🔥 ĐÃ NỔ HŨ {jackpot_hit_count} LẦN!"
            slot_status.value = status_msg
            slot_status.color = colors.GREEN_400 if net_profit >= 0 else colors.RED_400

            jackpot_text.value = f"🔥 QUỸ HŨ JACKPOT: {format_currency(jackpot_pool)} Xu Vàng"
            page.update()

        slot_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text("🎰 PENTA SEVEN 5x5 (NERFED RATIO 5:2:3)", size=18, weight=ft.FontWeight.BOLD, color=colors.AMBER_300),
                ft.Container(expand=True),
                ft.Text(f"💰 Số dư: {format_currency(current_user['xuvang'])} Xu", size=14, color=colors.GREEN_400, weight=ft.FontWeight.BOLD)
            ]),
            ft.Divider(height=5),
            jackpot_text,
            slot_status,
            win_display,
            ft.Container(content=grid_container, alignment=get_alignment_center(), padding=10),
            ft.Row([
                bet_dropdown_slot,
                spins_count_dropdown,
                SafeButton("QUAY NGAY", on_click=spin_slot, bgcolor=colors.AMBER_800, width=140)
            ], alignment=get_main_axis_align("CENTER"), spacing=10)
        ], expand=True, spacing=10)

        page.add(slot_layout)
        page.update()

    # ============================================================
    # VIEW: LẬP PHÒNG / VÀO PHÒNG MULTIPLAYER
    # ============================================================
    room_id_input = ft.TextField(label="Nhập ID phòng (6 chữ số)", width=220, max_length=6)
    bet_dropdown = ft.Dropdown(
        label="Chọn mức cược bàn chơi",
        width=280,
        options=[
            ft.dropdown.Option("50000", "50k Xu Vàng"),
            ft.dropdown.Option("100000", "100k Xu Vàng"),
            ft.dropdown.Option("500000", "500k Xu Vàng"),
            ft.dropdown.Option("5000000", "5 Triệu Xu Vàng"),
            ft.dropdown.Option("10000000", "10 Triệu Xu Vàng"),
            ft.dropdown.Option("50000000", "50 Triệu Xu Vàng"),
            ft.dropdown.Option("100000000", "100 Triệu Xu Vàng"),
            ft.dropdown.Option("500000000", "500 Triệu Xu Vàng"),
            ft.dropdown.Option("1000000000", "1 Tỷ Xu Vàng"),
        ],
        value="50000"
    )
    lobby_status_msg = ft.Text("", color=colors.RED_400)

    def cleanup_abandoned_rooms():
        try:
            res = requests.get(f"{FIRESTORE_URL}/rooms", timeout=5)
            if res.status_code == 200:
                docs = res.json().get("documents", [])
                current_time = int(time.time())
                for doc in docs:
                    name_path = doc.get("name", "")
                    rid = name_path.split("/")[-1]
                    fields = doc.get("fields", {})
                    last_active = int(fields.get("last_active", {}).get("integerValue", 0))
                    if current_time - last_active > 15:
                        requests.delete(f"{FIRESTORE_URL}/rooms/{rid}", timeout=3)
        except Exception as e:
            print("Lỗi cleanup_abandoned_rooms:", e)

    def fetch_room_data(room_id):
        try:
            res = requests.get(f"{FIRESTORE_URL}/rooms/{room_id}", timeout=5)
            if res.status_code == 200:
                return res.json().get("fields", {})
        except Exception as e:
            print("Lỗi fetch_room_data:", e)
        return None

    def update_room_players_firestore(room_id, players_list):
        array_values = []
        for p in players_list:
            array_values.append({
                "mapValue": {
                    "fields": {
                        "username": {"stringValue": p["username"]},
                        "is_ready": {"booleanValue": p["is_ready"]},
                        "is_host": {"booleanValue": p["is_host"]}
                    }
                }
            })
        
        current_time = str(int(time.time()))
        payload = {
            "fields": {
                "players": {"arrayValue": {"values": array_values}},
                "last_active": {"integerValue": current_time}
            }
        }
        try:
            requests.patch(f"{FIRESTORE_URL}/rooms/{room_id}?updateMask.fieldPaths=players&updateMask.fieldPaths=last_active", json=payload, timeout=5)
        except Exception as e:
            print("Lỗi update_room_players_firestore:", e)

    def create_room_click(e):
        nonlocal current_room_id
        bet_val = int(bet_dropdown.value)

        if current_user["xuvang"] < bet_val * 2:
            lobby_status_msg.value = f"Số dư không đủ! Cần tối thiểu {format_currency(bet_val * 2)} Xu Vàng để làm Nhà cái."
            page.update()
            return

        new_room_id = str(random.randint(100000, 999999))
        current_time = str(int(time.time()))

        room_payload = {
            "fields": {
                "room_id": {"stringValue": new_room_id},
                "host": {"stringValue": current_user["username"]},
                "status": {"stringValue": "waiting"},
                "bet_amount": {"integerValue": str(bet_val)},
                "last_active": {"integerValue": current_time},
                "players": {
                    "arrayValue": {
                        "values": [{
                            "mapValue": {
                                "fields": {
                                    "username": {"stringValue": current_user["username"]},
                                    "is_ready": {"booleanValue": True},
                                    "is_host": {"booleanValue": True}
                                }
                            }
                        }]
                    }
                }
            }
        }

        try:
            res = requests.post(f"{FIRESTORE_URL}/rooms?documentId={new_room_id}", json=room_payload, timeout=5)
            if res.status_code == 200:
                current_room_id = new_room_id
                show_room_waiting_view(new_room_id)
            else:
                lobby_status_msg.value = "Không thể tạo phòng!"
                page.update()
        except Exception as ex:
            lobby_status_msg.value = f"Lỗi: {ex}"
            page.update()

    def join_room_by_id_click(e):
        nonlocal current_room_id
        rid = room_id_input.value.strip()
        if len(rid) != 6:
            lobby_status_msg.value = "ID phòng phải gồm đúng 6 chữ số!"
            page.update()
            return

        room_data = fetch_room_data(rid)
        if not room_data:
            lobby_status_msg.value = "Phòng không tồn tại!"
            page.update()
            return

        existing_players = []
        raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
        for vp in raw_players:
            p_map = vp.get("mapValue", {}).get("fields", {})
            existing_players.append({
                "username": p_map.get("username", {}).get("stringValue", ""),
                "is_ready": p_map.get("is_ready", {}).get("booleanValue", False),
                "is_host": p_map.get("is_host", {}).get("booleanValue", False)
            })

        usernames = [p["username"] for p in existing_players]
        if current_user["username"] not in usernames:
            if len(existing_players) >= 5:
                lobby_status_msg.value = "Phòng đã đầy (Tối đa 5 người)!"
                page.update()
                return
            existing_players.append({
                "username": current_user["username"],
                "is_ready": False,
                "is_host": False
            })
            update_room_players_firestore(rid, existing_players)

        current_room_id = rid
        show_room_waiting_view(rid)

    def show_room_lobby_view(game_title="Blackjack Multiplayer"):
        nonlocal in_room_waiting
        in_room_waiting = False
        threading.Thread(target=cleanup_abandoned_rooms, daemon=True).start()

        page.clean()
        lobby_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Quay lại", on_click=lambda e: show_dashboard_view()),
                ft.Text(f"🏠 SẢNH PHÒNG - {game_title}", size=20, weight=ft.FontWeight.BOLD, color=colors.BLUE_200)
            ]),
            ft.Divider(height=10, color=colors.TRANSPARENT),
            lobby_status_msg,
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("✨ TẠO PHÒNG MỚI (BẠN LÀM NHÀ CÁI)", size=15, weight=ft.FontWeight.BOLD, color=colors.AMBER_300),
                        bet_dropdown,
                        SafeButton("Tạo Phòng", on_click=create_room_click, width=280, bgcolor=colors.GREEN_700)
                    ], spacing=15),
                    padding=20, bgcolor=colors.GREY_900, border_radius=10, expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("🔍 THAM GIA BẰNG ID PHÒNG", size=15, weight=ft.FontWeight.BOLD, color=colors.BLUE_300),
                        room_id_input,
                        SafeButton("Vào Phòng", on_click=join_room_by_id_click, width=220, bgcolor=colors.BLUE_700)
                    ], spacing=15),
                    padding=20, bgcolor=colors.GREY_900, border_radius=10, expand=True
                )
            ], alignment=get_main_axis_align("SPACE_BETWEEN"))
        ], expand=True, spacing=15)
        page.add(lobby_layout)
        page.update()

    # ============================================================
    # VIEW: PHÒNG CHỜ TRONG BÀN BLACKJACK
    # ============================================================
    def show_room_waiting_view(room_id):
        nonlocal in_room_waiting
        in_room_waiting = True
        page.clean()

        players_list_view = ft.ListView(expand=True, spacing=10)
        start_game_btn = SafeButton("Bắt Đầu Trận Đấu", on_click=lambda e: start_blackjack_game_action(room_id), bgcolor=colors.AMBER_800, disabled=True)

        def refresh_room_ui():
            room_data = fetch_room_data(room_id)
            if not room_data: return

            status = room_data.get("status", {}).get("stringValue", "waiting")
            if status == "playing":
                show_blackjack_game_view(room_id)
                return

            host_name = room_data.get("host", {}).get("stringValue", "")
            is_host = (current_user["username"] == host_name)
            
            raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
            players_list_view.controls.clear()

            all_ready = True
            total_players = len(raw_players)

            for vp in raw_players:
                p_map = vp.get("mapValue", {}).get("fields", {})
                p_user = p_map.get("username", {}).get("stringValue", "")
                p_ready = p_map.get("is_ready", {}).get("booleanValue", False)
                p_host = p_map.get("is_host", {}).get("booleanValue", False)

                if not p_ready: all_ready = False

                sub_text = "Trạng thái: Đã sẵn sàng" if p_ready else "Trạng thái: Chưa sẵn sàng"
                sub_color = colors.GREEN_300 if p_ready else colors.ORANGE_300

                trailing_widget = None
                if is_host and p_user != current_user["username"]:
                    trailing_widget = SafeButton("Kick", on_click=lambda e, u=p_user: kick_user(u), bgcolor=colors.RED_700)

                players_list_view.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(icons.ACCOUNT_CIRCLE, color=colors.AMBER_400 if p_host else colors.GREEN_400),
                        title=ft.Text(f"{p_user} {'(Nhà Cái)' if p_host else '(Nhà Con)'} {'(Bạn)' if p_user == current_user['username'] else ''}", color=colors.WHITE, weight=ft.FontWeight.BOLD),
                        subtitle=ft.Text(sub_text, color=sub_color),
                        trailing=trailing_widget
                    )
                )

            if is_host and total_players >= 2 and all_ready:
                start_game_btn.disabled = False
                start_game_btn.bgcolor = colors.GREEN_600
            else:
                start_game_btn.disabled = True
                start_game_btn.bgcolor = colors.GREY_700

            page.update()

        def start_blackjack_game_action(rid):
            try:
                deck = create_deck()
                room_data = fetch_room_data(rid)
                raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
                host_name = room_data.get("host", {}).get("stringValue", "")

                player_names = [vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "") for vp in raw_players]
                turn_order = [p for p in player_names if p != host_name] + [host_name]
                first_turn = turn_order[0]

                deck_str_list = [c.id for c in deck]
                payload_fields = {
                    "status": {"stringValue": "playing"},
                    "current_turn": {"stringValue": first_turn},
                    "deck": {"arrayValue": {"values": [{"stringValue": cid} for cid in deck_str_list]}},
                    "game_log": {"stringValue": f"Ván Xì Dách bắt đầu! Đến lượt [{first_turn}] rút hoặc dằn bài."}
                }

                for p_user in player_names:
                    card1 = deck.pop(0).id
                    card2 = deck.pop(0).id
                    payload_fields[f"hand_{p_user}"] = {"arrayValue": {"values": [{"stringValue": card1}, {"stringValue": card2}]}}
                    payload_fields[f"status_{p_user}"] = {"stringValue": "playing"}

                payload_fields["deck"] = {"arrayValue": {"values": [{"stringValue": c.id} for c in deck]}}

                requests.patch(f"{FIRESTORE_URL}/rooms/{rid}?updateMask.fieldPaths=" + "&updateMask.fieldPaths=".join(payload_fields.keys()), json={"fields": payload_fields}, timeout=5)
                show_blackjack_game_view(rid)

            except Exception as e:
                print("Lỗi khởi tạo bàn chơi Blackjack:", e)

        def kick_user(target_user):
            room_data = fetch_room_data(room_id)
            if not room_data: return
            raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
            new_players = [
                {
                    "username": vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", ""),
                    "is_ready": vp.get("mapValue", {}).get("fields", {}).get("is_ready", {}).get("booleanValue", False),
                    "is_host": vp.get("mapValue", {}).get("fields", {}).get("is_host", {}).get("booleanValue", False)
                } for vp in raw_players if vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "") != target_user
            ]
            update_room_players_firestore(room_id, new_players)
            refresh_room_ui()

        def toggle_ready(e):
            room_data = fetch_room_data(room_id)
            if not room_data: return
            raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
            new_players = []
            for vp in raw_players:
                p_map = vp.get("mapValue", {}).get("fields", {})
                uname = p_map.get("username", {}).get("stringValue", "")
                is_r = p_map.get("is_ready", {}).get("booleanValue", False)
                if uname == current_user["username"]: is_r = not is_r
                new_players.append({"username": uname, "is_ready": is_r, "is_host": p_map.get("is_host", {}).get("booleanValue", False)})
            update_room_players_firestore(room_id, new_players)
            refresh_room_ui()

        def leave_room(e):
            nonlocal in_room_waiting
            in_room_waiting = False
            room_data = fetch_room_data(room_id)
            if room_data:
                host_name = room_data.get("host", {}).get("stringValue", "")
                raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
                new_players = [
                    {
                        "username": vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", ""),
                        "is_ready": vp.get("mapValue", {}).get("fields", {}).get("is_ready", {}).get("booleanValue", False),
                        "is_host": vp.get("mapValue", {}).get("fields", {}).get("is_host", {}).get("booleanValue", False)
                    } for vp in raw_players if vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "") != current_user["username"]
                ]
                if current_user["username"] == host_name or len(new_players) == 0:
                    try: requests.delete(f"{FIRESTORE_URL}/rooms/{room_id}", timeout=5)
                    except: pass
                else:
                    update_room_players_firestore(room_id, new_players)
            show_room_lobby_view()

        def room_sync_loop():
            nonlocal in_room_waiting
            while in_room_waiting:
                time.sleep(3)
                if not in_room_waiting: break
                refresh_room_ui()

        room_info_header = ft.Row([
            ft.Text(f"🔑 PHÒNG CHỜ BLACKJACK - ID: {room_id}", size=18, weight=ft.FontWeight.BOLD, color=colors.YELLOW_300),
            start_game_btn
        ], alignment=get_main_axis_align("SPACE_BETWEEN"))

        waiting_layout = ft.Column([
            room_info_header,
            ft.Divider(height=10),
            ft.Text("Danh sách thành viên bàn chơi:", color=colors.GREY_400),
            ft.Container(content=players_list_view, bgcolor=colors.GREY_900, border_radius=10, padding=10, height=280),
            ft.Row([
                SafeButton("Sẵn Sàng / Hủy", on_click=toggle_ready, bgcolor=colors.BLUE_600),
                SafeButton("Rời Phòng", on_click=leave_room, bgcolor=colors.RED_700),
            ], alignment=get_main_axis_align("SPACE_BETWEEN"))
        ], expand=True, spacing=15)

        page.add(waiting_layout)
        page.update()
        refresh_room_ui()
        threading.Thread(target=room_sync_loop, daemon=True).start()

    # ============================================================
    # VIEW: BÀN CHƠI BLACKJACK MULTIPLAYER
    # ============================================================
    def show_blackjack_game_view(room_id):
        nonlocal in_room_waiting
        in_room_waiting = False
        page.clean()

        is_game_active = True
        turn_status_text = ft.Text("Đang tải bàn chơi...", size=16, weight=ft.FontWeight.BOLD, color=colors.YELLOW_300)
        game_log_text = ft.Text("Nhật ký trận đấu...", size=13, color=colors.GREY_300)

        players_area = ft.Row([], alignment=get_main_axis_align("CENTER"), spacing=15, wrap=True)

        def parse_card_str(c_str):
            rank = c_str[:-1]
            suit = c_str[-1]
            return Card(rank, suit)

        def make_card_ui(card_obj):
            card_color = colors.RED_600 if card_obj.is_red() else colors.BLACK
            return ft.Container(
                content=ft.Column([
                    ft.Text(card_obj.rank, size=16, weight=ft.FontWeight.BOLD, color=card_color),
                    ft.Text(card_obj.suit, size=20, color=card_color),
                ], alignment=get_main_axis_align("CENTER"), horizontal_alignment=get_cross_axis_align("CENTER"), spacing=0),
                width=48, height=72, bgcolor=colors.WHITE, border_radius=6,
                border=ft.border.all(1, colors.GREY_400)
            )

        def handle_hit(e):
            room_data = fetch_room_data(room_id)
            if not room_data: return

            curr_turn = room_data.get("current_turn", {}).get("stringValue", "")
            if curr_turn != current_user["username"]:
                show_toast("Chưa tới lượt của bạn!")
                return

            raw_deck = room_data.get("deck", {}).get("arrayValue", {}).get("values", [])
            deck_list = [v.get("stringValue", "") for v in raw_deck]

            if not deck_list:
                show_toast("Đã hết bài trong bộ!")
                return

            drawn_card = deck_list.pop(0)
            raw_hand = room_data.get(f"hand_{current_user['username']}", {}).get("arrayValue", {}).get("values", [])
            my_hand_str = [v.get("stringValue", "") for v in raw_hand] + [drawn_card]
            
            cards_obj = [parse_card_str(c) for c in my_hand_str]
            score, label = calculate_bj_score(cards_obj)

            payload = {
                "fields": {
                    f"hand_{current_user['username']}": {"arrayValue": {"values": [{"stringValue": cid} for cid in my_hand_str]}},
                    "deck": {"arrayValue": {"values": [{"stringValue": cid} for cid in deck_list]}},
                    "game_log": {"stringValue": f"[{current_user['username']}] RÚT THÊM LÁ BÀI ({label})."}
                }
            }

            if score > 21 or len(my_hand_str) >= 5 or score >= 28:
                payload["fields"][f"status_{current_user['username']}"] = {"stringValue": "stand"}
                advance_turn(room_data, payload)
            else:
                requests.patch(f"{FIRESTORE_URL}/rooms/{room_id}?updateMask.fieldPaths=" + "&updateMask.fieldPaths=".join(payload["fields"].keys()), json=payload, timeout=5)

        def handle_stand(e):
            room_data = fetch_room_data(room_id)
            if not room_data: return

            curr_turn = room_data.get("current_turn", {}).get("stringValue", "")
            if curr_turn != current_user["username"]:
                show_toast("Chưa tới lượt của bạn!")
                return

            payload = {
                "fields": {
                    f"status_{current_user['username']}": {"stringValue": "stand"},
                    "game_log": {"stringValue": f"[{current_user['username']}] ĐÃ DẰN BÀI."}
                }
            }
            advance_turn(room_data, payload)

        def advance_turn(room_data, payload):
            host_name = room_data.get("host", {}).get("stringValue", "")
            raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
            player_names = [vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "") for vp in raw_players]
            
            turn_order = [p for p in player_names if p != host_name] + [host_name]
            curr_idx = turn_order.index(current_user["username"])

            if curr_idx + 1 < len(turn_order):
                next_user = turn_order[curr_idx + 1]
                payload["fields"]["current_turn"] = {"stringValue": next_user}
                requests.patch(f"{FIRESTORE_URL}/rooms/{room_id}?updateMask.fieldPaths=" + "&updateMask.fieldPaths=".join(payload["fields"].keys()), json=payload, timeout=5)
            else:
                execute_blackjack_settlement(room_data)

        def execute_blackjack_settlement(room_data):
            nonlocal is_game_active
            is_game_active = False

            host_name = room_data.get("host", {}).get("stringValue", "")
            bet_val = int(room_data.get("bet_amount", {}).get("integerValue", 50000))
            raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
            player_names = [vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "") for vp in raw_players]

            host_hand_raw = room_data.get(f"hand_{host_name}", {}).get("arrayValue", {}).get("values", [])
            host_cards = [parse_card_str(v.get("stringValue", "")) for v in host_hand_raw]
            host_score, host_label = calculate_bj_score(host_cards)

            summary_logs = [f"👑 Nhà cái [{host_name}]: {host_label}"]

            host_doc = get_user_doc(host_name)
            host_gold = host_doc["xuvang"] if host_doc else 0

            for p_user in player_names:
                if p_user == host_name: continue

                p_hand_raw = room_data.get(f"hand_{p_user}", {}).get("arrayValue", {}).get("values", [])
                p_cards = [parse_card_str(v.get("stringValue", "")) for v in p_hand_raw]
                p_score, p_label = calculate_bj_score(p_cards)

                p_doc = get_user_doc(p_user)
                p_gold = p_doc["xuvang"] if p_doc else 0

                is_p_win = False
                is_draw = False

                if p_score > 21 and host_score > 21:
                    is_draw = True
                elif p_score > 21:
                    is_p_win = False
                elif host_score > 21:
                    is_p_win = True
                else:
                    if p_score > host_score: is_p_win = True
                    elif p_score < host_score: is_p_win = False
                    else: is_draw = True

                if is_draw:
                    summary_logs.append(f"• {p_user} ({p_label}): Hòa Nhà cái")
                elif is_p_win:
                    win_amt = min(host_gold, bet_val)
                    p_gold += win_amt
                    host_gold -= win_amt
                    update_user_fields(p_user, {"xuvang": {"integerValue": str(p_gold)}})
                    summary_logs.append(f"• {p_user} ({p_label}): THẮNG +{format_currency(win_amt)}")
                else:
                    lose_amt = min(p_gold, bet_val)
                    p_gold -= lose_amt
                    host_gold += lose_amt
                    
                    # Cộng XP khi tiêu hao vàng cược bàn chơi (1000 vàng = 1 XP)
                    if p_user == current_user["username"]:
                        new_total_xp = add_user_xp_and_gold(current_user, lose_amt, 0)
                        current_user["total_xp"] = new_total_xp
                        update_user_fields(p_user, {
                            "xuvang": {"integerValue": str(p_gold)},
                            "total_xp": {"integerValue": str(new_total_xp)}
                        })
                    else:
                        update_user_fields(p_user, {"xuvang": {"integerValue": str(p_gold)}})

                    summary_logs.append(f"• {p_user} ({p_label}): THUA -{format_currency(lose_amt)}")

            update_user_fields(host_name, {"xuvang": {"integerValue": str(host_gold)}})

            end_msg = "🏁 KẾT QUẢ VÁN BLACKJACK:\n" + "\n".join(summary_logs)
            payload = {
                "fields": {
                    "status": {"stringValue": "waiting"},
                    "game_log": {"stringValue": end_msg}
                }
            }
            requests.patch(f"{FIRESTORE_URL}/rooms/{room_id}?updateMask.fieldPaths=status&updateMask.fieldPaths=game_log", json=payload, timeout=5)
            show_room_waiting_view(room_id)

        def bj_sync_loop():
            nonlocal is_game_active
            while is_game_active:
                time.sleep(1.5)
                if not is_game_active: break

                room_data = fetch_room_data(room_id)
                if not room_data: continue

                status = room_data.get("status", {}).get("stringValue", "waiting")
                if status == "waiting":
                    show_room_waiting_view(room_id)
                    break

                curr_turn = room_data.get("current_turn", {}).get("stringValue", "")
                turn_status_text.value = f"👉 LƯỢT CHƠI: [{curr_turn}] {'(BẠN)' if curr_turn == current_user['username'] else ''}"
                game_log_text.value = room_data.get("game_log", {}).get("stringValue", "")

                raw_players = room_data.get("players", {}).get("arrayValue", {}).get("values", [])
                players_area.controls.clear()

                for vp in raw_players:
                    uname = vp.get("mapValue", {}).get("fields", {}).get("username", {}).get("stringValue", "")
                    is_h = vp.get("mapValue", {}).get("fields", {}).get("is_host", {}).get("booleanValue", False)

                    p_hand_raw = room_data.get(f"hand_{uname}", {}).get("arrayValue", {}).get("values", [])
                    p_cards = [parse_card_str(v.get("stringValue", "")) for v in p_hand_raw]
                    score, label = calculate_bj_score(p_cards)

                    cards_row = ft.Row([make_card_ui(c) for c in p_cards], spacing=3)

                    p_card_box = ft.Container(
                        content=ft.Column([
                            ft.Text(f"{'👑 Nhà Cái: ' if is_h else '👤 '}{uname}", size=14, weight=ft.FontWeight.BOLD, color=colors.AMBER_300 if is_h else colors.WHITE),
                            cards_row,
                            ft.Text(label, size=12, color=colors.GREEN_300, weight=ft.FontWeight.BOLD)
                        ], horizontal_alignment=get_cross_axis_align("CENTER"), spacing=5),
                        padding=10, bgcolor=colors.GREY_900, border_radius=10, width=220
                    )
                    players_area.controls.append(p_card_box)

                page.update()

        bj_layout = ft.Column([
            ft.Row([
                ft.IconButton(icons.ARROW_BACK, tooltip="Rời bàn", on_click=lambda e: show_dashboard_view()),
                ft.Text(f"♠️ BÀN BLACKJACK MULTIPLAYER - ID: {room_id}", size=18, weight=ft.FontWeight.BOLD, color=colors.AMBER_300),
            ]),
            ft.Divider(height=5),
            turn_status_text,
            game_log_text,
            ft.Container(content=players_area, padding=10, bgcolor=colors.GREEN_900, border_radius=12, min_height=260),
            ft.Row([
                SafeButton("RÚT (HIT)", on_click=handle_hit, bgcolor=colors.GREEN_700, width=150),
                SafeButton("DẰN (STAND)", on_click=handle_stand, bgcolor=colors.AMBER_800, width=150),
            ], alignment=get_main_axis_align("CENTER"), spacing=20)
        ], expand=True, spacing=10)

        page.add(bj_layout)
        page.update()
        threading.Thread(target=bj_sync_loop, daemon=True).start()

    # ============================================================
    # VIEW: DASHBOARD
    # ============================================================
    def create_game_card(title, desc, icon_data, bg_color):
        if "Blackjack" in title:
            click_action = lambda e: show_room_lobby_view("Blackjack Multiplayer")
        elif "Penta Seven" in title:
            click_action = lambda e: show_penta_seven_slot_view()
        elif "Bảng Xếp Hạng" in title:
            click_action = lambda e: show_leaderboard_view()
        elif "Vòng Quay" in title:
            click_action = lambda e: show_lucky_wheel_view()
        elif "Rắn Săn Mồi" in title:
            click_action = lambda e: show_snake_game_view()
        elif "Pikachu" in title:
            click_action = lambda e: show_pikachu_game_view()
        else:
            click_action = lambda e: show_toast(f"Đang mở {title}...")

        return ft.Container(
            content=ft.Column([
                ft.Icon(icon_data, size=40, color=colors.WHITE),
                ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=colors.WHITE, text_align=get_text_align("CENTER")),
                ft.Text(desc, size=11, color=colors.WHITE70, text_align=get_text_align("CENTER")),
                SafeButton("Vào Bàn", on_click=click_action)
            ], alignment=get_main_axis_align("CENTER"), horizontal_alignment=get_cross_axis_align("CENTER"), spacing=5),
            bgcolor=bg_color,
            border_radius=12,
            padding=10,
            width=280,
            height=160
        )

    def show_dashboard_view():
        nonlocal in_room_waiting
        in_room_waiting = False
        page.clean()
        sys_data = get_system_data()
        marquee_text.value = f"📢 {sys_data['marquee_message']}  |  🔥 HŨ JACKPOT HỆ THỐNG: {sys_data['jackpot_pool']:,} VNĐ"

        level, cur_xp, next_xp = calculate_level_info(current_user.get("total_xp", 0))
        badge_title, badge_color, text_color = get_level_badge_and_color(level, current_user.get("role", "user"))
        progress_val = cur_xp / next_xp if next_xp > 0 else 1.0

        now_ts = int(time.time())
        premix_exp = current_user.get("premix_expires", 0)
        spremix_exp = current_user.get("spremix_expires", 0)
        has_premix = premix_exp > now_ts
        has_spremix = spremix_exp > now_ts

        if has_premix and has_spremix:
            tier_display = "👑🌟 Premix & SPremix"
            tier_badge_color = colors.PURPLE_ACCENT
        elif has_spremix:
            tier_display = "🌟 SPremix"
            tier_badge_color = colors.INDIGO_ACCENT
        elif has_premix:
            tier_display = "👑 Premix"
            tier_badge_color = colors.AMBER_ACCENT
        else:
            tier_display = "👤 Thường"
            tier_badge_color = colors.GREY_600

        header_info = ft.Row([
            ft.Icon(icons.ACCOUNT_CIRCLE, size=40, color=badge_color),
            ft.Column([
                ft.Row([
                    ft.Text(current_user["username"], size=18, weight=ft.FontWeight.BOLD, color=text_color),
                    ft.Container(
                        content=ft.Text(f"Lv.{level} | {badge_title}", size=11, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                        bgcolor=badge_color,
                        padding=get_padding_symmetric(horizontal=8, vertical=2),
                        border_radius=10
                    ),
                    ft.Container(
                        content=ft.Text(tier_display, size=11, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                        bgcolor=tier_badge_color,
                        padding=get_padding_symmetric(horizontal=8, vertical=2),
                        border_radius=10
                    )
                ]),
                ft.Row([
                    ft.Text(f"💵 VNĐ: {current_user.get('balance', 0):,}đ | 💰 Xu Vàng: {current_user.get('xuvang', 0):,}", color=colors.GREEN_400, weight=ft.FontWeight.BOLD),
                    ft.Text(f"XP: {cur_xp}/{next_xp}", size=12, color=colors.GREY_400),
                ]),
                ft.ProgressBar(value=progress_val, width=240, color=badge_color, bgcolor=colors.GREY_800)
            ], spacing=2)
        ])

        top_bar = ft.Container(
            content=ft.Row([
                header_info,
                ft.Row([
                    SafeButton("🛒 Cửa Hàng", on_click=lambda e: show_store_view(), bgcolor=colors.PURPLE_700),
                    ft.IconButton(icons.LOGOUT, tooltip="Đăng xuất", on_click=lambda e: show_login_view())
                ], spacing=10)
            ], alignment=get_main_axis_align("SPACE_BETWEEN")),
            padding=12,
            bgcolor=colors.GREY_900,
            border_radius=10,
            margin=get_margin_only(bottom=10)
        )

        game_tiles_row = ft.Row(
            wrap=True,
            spacing=15,
            run_spacing=15,
            controls=[
                create_game_card("🎰 Penta Seven 5x5", "Slot Tiering (Nerfed 5:2:3)", icons.CASINO, colors.PURPLE_700),
                create_game_card("🎰 Vòng Quay May Mắn", "3 Mức quay riêng biệt & Nổ Hũ Jackpot", icons.AUTO_MODE, colors.PURPLE_600),
                create_game_card("♠️ Blackjack Realtime", "Xì dách Đa người chơi Realtime", icons.STYLE, colors.BLUE_800),
                create_game_card("🐍 Rắn Săn Mồi (Farm)", "Game Farm Xu Vàng (Premix x300% XP)", icons.VIDEOGAME_ASSET, colors.GREEN_700),
                create_game_card("🧩 Pikachu / Xếp Hình", "Mini-game thư giãn kiếm quà", icons.EXTENSION, colors.AMBER_700),
                create_game_card("🏆 Bảng Xếp Hạng Tháng", "Top Nạp VNĐ & Xu Vàng Farm", icons.LEADERBOARD, colors.TEAL_700),
            ]
        )

        page.add(
            top_bar,
            marquee_container,
            ft.Text("🎮 DANH SÁCH BÀN CHƠI & MINI-GAME", size=16, weight=ft.FontWeight.BOLD, color=colors.GREY_300),
            game_tiles_row
        )
        page.update()

    show_login_view()

if __name__ == "__main__":
    import os  # Nhớ kiểm tra xem ở đầu file đã có dòng "import os" chưa nhé, nếu chưa thì thêm vào

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")