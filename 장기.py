import socket
import threading
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

# 보드 크기: 10행 (0~9), 9열 (0~8)
ROWS = 10
COLS = 9

CHO = "초"  # Blue / 초나라 (하단 기본)
HAN = "한"  # Red / 한나라 (상단 기본)

PALACE_HAN = {(r, c) for r in range(0, 3) for c in range(3, 6)}
PALACE_CHO = {(r, c) for r in range(7, 10) for c in range(3, 6)}

PALACE_DIAG_EDGES = {
    (0, 3): [(1, 4)], (0, 5): [(1, 4)],
    (2, 3): [(1, 4)], (2, 5): [(1, 4)],
    (1, 4): [(0, 3), (0, 5), (2, 3), (2, 5)],
    (7, 3): [(8, 4)], (7, 5): [(8, 4)],
    (9, 3): [(8, 4)], (9, 5): [(8, 4)],
    (8, 4): [(7, 3), (7, 5), (9, 3), (9, 5)],
}

class JanggiBoard:
    def __init__(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.turn = CHO
        self.setup_board()

    def setup_board(self):
        # 한나라 (상단)
        self.board[0][0] = (HAN, "車")
        self.board[0][1] = (HAN, "馬")
        self.board[0][2] = (HAN, "象")
        self.board[0][3] = (HAN, "士")
        self.board[0][5] = (HAN, "士")
        self.board[0][6] = (HAN, "象")
        self.board[0][7] = (HAN, "馬")
        self.board[0][8] = (HAN, "車")
        self.board[1][4] = (HAN, "楚")
        self.board[2][1] = (HAN, "包")
        self.board[2][7] = (HAN, "包")
        for c in [0, 2, 4, 6, 8]:
            self.board[3][c] = (HAN, "兵")

        # 초나라 (하단)
        self.board[9][0] = (CHO, "車")
        self.board[9][1] = (CHO, "馬")
        self.board[9][2] = (CHO, "象")
        self.board[9][3] = (CHO, "士")
        self.board[9][5] = (CHO, "士")
        self.board[9][6] = (CHO, "象")
        self.board[9][7] = (CHO, "馬")
        self.board[9][8] = (CHO, "車")
        self.board[8][4] = (CHO, "漢")
        self.board[7][1] = (CHO, "包")
        self.board[7][7] = (CHO, "包")
        for c in [0, 2, 4, 6, 8]:
            self.board[6][c] = (CHO, "卒")

    def is_in_bounds(self, r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    def get_valid_moves(self, r, c):
        piece = self.board[r][c]
        if not piece or piece[0] != self.turn:
            return []

        camp, ptype = piece
        moves = []

        if ptype in ("卒", "兵"):
            fwd = -1 if camp == CHO else 1
            candidates = [(r + fwd, c), (r, c - 1), (r, c + 1)]
            if (r, c) in PALACE_DIAG_EDGES:
                for nr, nc in PALACE_DIAG_EDGES[(r, c)]:
                    if (camp == CHO and nr < r) or (camp == HAN and nr > r):
                        candidates.append((nr, nc))
            for nr, nc in candidates:
                if self.is_in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if target is None or target[0] != camp:
                        moves.append((nr, nc))

        elif ptype == "車":
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                while self.is_in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if target is None:
                        moves.append((nr, nc))
                    else:
                        if target[0] != camp:
                            moves.append((nr, nc))
                        break
                    nr += dr
                    nc += dc
            if (r, c) in PALACE_DIAG_EDGES:
                palace = PALACE_CHO if (r, c) in PALACE_CHO else PALACE_HAN
                for nr, nc in PALACE_DIAG_EDGES[(r, c)]:
                    target = self.board[nr][nc]
                    if target is None:
                        moves.append((nr, nc))
                        dr, dc = nr - r, nc - c
                        nnr, nnc = nr + dr, nc + dc
                        if (nnr, nnc) in palace:
                            tgt2 = self.board[nnr][nnc]
                            if tgt2 is None or tgt2[0] != camp:
                                moves.append((nnr, nnc))
                    elif target[0] != camp:
                        moves.append((nr, nc))

        elif ptype == "包":
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                bridge_found = False
                nr, nc = r + dr, c + dc
                while self.is_in_bounds(nr, nc):
                    target = self.board[nr][nc]
                    if not bridge_found:
                        if target is not None:
                            if target[1] == "包":
                                break
                            bridge_found = True
                    else:
                        if target is None:
                            moves.append((nr, nc))
                        else:
                            if target[0] != camp and target[1] != "包":
                                moves.append((nr, nc))
                            break
                    nr += dr
                    nc += dc

        elif ptype == "馬":
            steps = [
                ((-1, 0), (-2, -1), (-2, 1)),
                ((1, 0), (2, -1), (2, 1)),
                ((0, -1), (-1, -2), (1, -2)),
                ((0, 1), (-1, 2), (1, 2)),
            ]
            for (br, bc), d1, d2 in steps:
                mr, mc = r + br, c + bc
                if self.is_in_bounds(mr, mc) and self.board[mr][mc] is None:
                    for tr, tc in [(r + d1[0], c + d1[1]), (r + d2[0], c + d2[1])]:
                        if self.is_in_bounds(tr, tc):
                            target = self.board[tr][tc]
                            if target is None or target[0] != camp:
                                moves.append((tr, tc))

        elif ptype == "象":
            steps = [
                ((-1, 0), [(-2, -1), (-3, -2)], [(-2, 1), (-3, 2)]),
                ((1, 0), [(2, -1), (3, -2)], [(2, 1), (3, 2)]),
                ((0, -1), [(-1, -2), (-2, -3)], [(1, -2), (2, -3)]),
                ((0, 1), [(-1, 2), (-2, 3)], [(1, 2), (2, 3)]),
            ]
            for (br, bc), branch1, branch2 in steps:
                mr, mc = r + br, c + bc
                if self.is_in_bounds(mr, mc) and self.board[mr][mc] is None:
                    for path in (branch1, branch2):
                        w1r, w1c = r + path[0][0], c + path[0][1]
                        tr, tc = r + path[1][0], c + path[1][1]
                        if self.is_in_bounds(tr, tc) and self.board[w1r][w1c] is None:
                            target = self.board[tr][tc]
                            if target is None or target[0] != camp:
                                moves.append((tr, tc))

        elif ptype in ("楚", "漢", "士"):
            palace = PALACE_CHO if (r, c) in PALACE_CHO else PALACE_HAN
            adj = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
            if (r, c) in PALACE_DIAG_EDGES:
                adj.extend(PALACE_DIAG_EDGES[(r, c)])
            for nr, nc in adj:
                if (nr, nc) in palace:
                    target = self.board[nr][nc]
                    if target is None or target[0] != camp:
                        moves.append((nr, nc))

        return moves

    def make_move(self, r1, c1, r2, c2):
        valid = self.get_valid_moves(r1, c1)
        if (r2, c2) not in valid:
            return False, "규칙상 둘 수 없는 자리입니다."

        captured = self.board[r2][c2]
        self.board[r2][c2] = self.board[r1][c1]
        self.board[r1][c1] = None

        game_over = False
        winner = None
        if captured and captured[1] in ("楚", "漢"):
            game_over = True
            winner = self.turn

        self.turn = HAN if self.turn == CHO else CHO
        return True, (game_over, winner)


# ----------------------------------------------------
# 고해상도 그래픽 GUI
# ----------------------------------------------------
class JanggiGUI:
    PIECE_SIZE_RATIOS = {
        "楚": 0.43, "漢": 0.43,
        "車": 0.39, "包": 0.39, "馬": 0.375, "象": 0.375,
        "士": 0.33, "卒": 0.33, "兵": 0.33
    }

    @staticmethod
    def get_octagon_points(cx, cy, r):
        c = r * 0.42
        return [
            cx - r + c, cy - r,
            cx + r - c, cy - r,
            cx + r,     cy - r + c,
            cx + r,     cy + r - c,
            cx + r - c, cy + r,
            cx - r + c, cy + r,
            cx - r,     cy + r - c,
            cx - r,     cy - r + c,
        ]

    def __init__(self, root, mode="local", sock=None, my_camp=CHO, on_game_end=None):
        self.root = root
        self.mode = mode
        self.sock = sock
        self.my_camp = my_camp
        self.on_game_end = on_game_end
        self.game = JanggiBoard()
        self.selected_pos = None
        self.valid_moves = []
        self.last_move = None
        self.game_active = True

        # 온라인 대전 시 한나라는 판을 뒤집어서 자신의 진영이 항상 앞(아래)에 오도록 설정
        self.flip_view = (self.mode == "network" and self.my_camp == HAN)

        self.is_fullscreen = False

        title_suffix = "로컬 2인" if mode == "local" else f"온라인 대전 ({self.my_camp})"
        self.root.title(f"고해상도 장기 - {title_suffix} (F11: 전체화면, ESC: 창모드)")

        default_w = 720
        default_h = 800
        self.root.geometry(f"{default_w}x{default_h}")
        self.root.configure(bg="#221A15")
        self.root.minsize(500, 580)
        self.root.resizable(True, True)

        self.cell_size = 72
        self.offset_x = 64
        self.offset_y = 64
        self.board_rect = (0, 0, 0, 0)

        # 상단 알림 바 및 기권 버튼
        self.status_bar = tk.Frame(root, bg="#2C221C", height=50)
        self.status_bar.pack(side=tk.TOP, fill=tk.X)

        self.resign_btn = tk.Button(
            self.status_bar, text="기권", font=("Malgun Gothic", 10, "bold"),
            bg="#991B1B", fg="#FFFFFF", activebackground="#DC2626", activeforeground="#FFFFFF",
            relief="flat", cursor="hand2", padx=12, command=self.on_resign
        )
        self.resign_btn.pack(side=tk.RIGHT, padx=15, pady=8)

        self.status_label = tk.Label(
            self.status_bar, text="", font=("Malgun Gothic", 13, "bold"),
            bg="#2C221C", fg="#F2DFC0", pady=10
        )
        self.status_label.pack(side=tk.LEFT, padx=15)

        # 캔버스 보드판
        self.canvas = tk.Canvas(root, bg="#221A15", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_resize)
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.update_status()

        if self.mode == "network" and self.sock:
            self.network_thread = threading.Thread(target=self.receive_network_moves, daemon=True)
            self.network_thread.start()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes("-fullscreen", False)
        return "break"

    def on_resize(self, event):
        cw = max(event.width, 100)
        ch = max(event.height, 100)

        avail_w = cw * 0.88
        avail_h = ch * 0.88

        scale_x = avail_w / (COLS - 1)
        scale_y = avail_h / (ROWS - 1)
        self.cell_size = max(min(scale_x, scale_y), 32)

        total_grid_w = self.cell_size * (COLS - 1)
        total_grid_h = self.cell_size * (ROWS - 1)

        self.offset_x = (cw - total_grid_w) / 2
        self.offset_y = (ch - total_grid_h) / 2

        pad = self.cell_size * 0.75
        self.board_rect = (
            self.offset_x - pad,
            self.offset_y - pad,
            self.offset_x + total_grid_w + pad,
            self.offset_y + total_grid_h + pad
        )

        self.draw_board()

    def update_status(self):
        turn_str = f"차례: [{self.game.turn}]"
        fs_tip = "  [F11: 전체화면]"
        if self.mode == "network":
            role_str = f"내 진영: [{self.my_camp}]"
            state_str = " (내 차례)" if self.game.turn == self.my_camp else " (상대 차례)"
            self.status_label.config(text=f"{role_str}  |  {turn_str}{state_str}{fs_tip}")
        else:
            self.status_label.config(text=f"{turn_str}{fs_tip}")

    # 좌표 변환 함수 (회전 뷰 고려)
    def to_pixel(self, r, c):
        view_r = (ROWS - 1 - r) if self.flip_view else r
        view_c = (COLS - 1 - c) if self.flip_view else c
        return self.offset_x + view_c * self.cell_size, self.offset_y + view_r * self.cell_size

    def to_grid(self, x, y):
        col = round((x - self.offset_x) / self.cell_size)
        row = round((y - self.offset_y) / self.cell_size)
        if 0 <= row < ROWS and 0 <= col < COLS:
            px, py = self.offset_x + col * self.cell_size, self.offset_y + row * self.cell_size
            hit_r = self.cell_size * 0.44
            if (x - px) ** 2 + (y - py) ** 2 <= hit_r ** 2:
                actual_r = (ROWS - 1 - row) if self.flip_view else row
                actual_c = (COLS - 1 - col) if self.flip_view else col
                return actual_r, actual_c
        return None

    def draw_board(self):
        self.canvas.delete("all")

        bx1, by1, bx2, by2 = self.board_rect
        if bx2 <= bx1 or by2 <= by1:
            return

        frame_w = max(int(self.cell_size * 0.11), 3)
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="#A87236", outline="#633C14", width=frame_w)
        
        m1 = max(int(self.cell_size * 0.18), 4)
        self.canvas.create_rectangle(bx1 + m1, by1 + m1, bx2 - m1, by2 - m1, fill="#C69255", outline="#7F4D1B", width=2)
        
        m2 = max(int(self.cell_size * 0.28), 6)
        self.canvas.create_rectangle(bx1 + m2, by1 + m2, bx2 - m2, by2 - m2, fill="#D19C5B", outline="#E4B77C", width=1)

        line_color = "#3E220D"
        line_width = max(int(self.cell_size * 0.028), 1)

        for r in range(ROWS):
            x1, y = self.to_pixel(r, 0)
            x2, _ = self.to_pixel(r, COLS - 1)
            self.canvas.create_line(x1, y, x2, y, fill=line_color, width=line_width)

        for c in range(COLS):
            x, y1 = self.to_pixel(0, c)
            _, y2 = self.to_pixel(ROWS - 1, c)
            self.canvas.create_line(x, y1, x, y2, fill=line_color, width=line_width)

        for (r1, c1), (r2, c2) in [
            ((0, 3), (2, 5)), ((0, 5), (2, 3)),
            ((7, 3), (9, 5)), ((7, 5), (9, 3))
        ]:
            p1, p2 = self.to_pixel(r1, c1), self.to_pixel(r2, c2)
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=line_color, width=line_width)

        if self.last_move:
            lr1, lc1, lr2, lc2 = self.last_move
            x_prev, y_prev = self.to_pixel(lr1, lc1)
            x_cur, y_cur = self.to_pixel(lr2, lc2)
            r_prev = self.cell_size * 0.17
            r_cur = self.cell_size * 0.44
            self.canvas.create_oval(x_prev - r_prev, y_prev - r_prev, x_prev + r_prev, y_prev + r_prev, outline="#784A22", width=2)
            self.canvas.create_oval(x_cur - r_cur, y_cur - r_cur, x_cur + r_cur, y_cur + r_cur, outline="#EAB308", width=3)

        for mr, mc in self.valid_moves:
            mx, my = self.to_pixel(mr, mc)
            r_outer = self.cell_size * 0.19
            r_inner = self.cell_size * 0.055
            self.canvas.create_oval(mx - r_outer, my - r_outer, mx + r_outer, my + r_outer, fill="#34D399", outline="#059669", width=2)
            self.canvas.create_oval(mx - r_inner, my - r_inner, mx + r_inner, my + r_inner, fill="#FFFFFF", outline="")

        for r in range(ROWS):
            for c in range(COLS):
                piece = self.game.board[r][c]
                if not piece:
                    continue
                camp, name = piece
                x, y = self.to_pixel(r, c)
                
                ratio = self.PIECE_SIZE_RATIOS.get(name, 0.36)
                radius = self.cell_size * ratio

                is_selected = (self.selected_pos == (r, c))

                s_off_x = max(self.cell_size * 0.04, 2)
                s_off_y = max(self.cell_size * 0.055, 3)
                shadow_pts = self.get_octagon_points(x + s_off_x, y + s_off_y, radius)
                self.canvas.create_polygon(shadow_pts, fill="#5C3612", outline="")

                body_color = "#EAD1A6" if camp == CHO else "#DEBE99"
                pts = self.get_octagon_points(x, y, radius)
                outline_color = "#2563EB" if is_selected else "#422814"
                outline_w = max(int(self.cell_size * 0.055), 3) if is_selected else max(int(self.cell_size * 0.028), 2)
                self.canvas.create_polygon(pts, fill=body_color, outline=outline_color, width=outline_w)

                inner_pts = self.get_octagon_points(x, y, radius - max(self.cell_size * 0.055, 3))
                self.canvas.create_polygon(inner_pts, fill="", outline="#F7EADB", width=1)

                fg_color = "#0B3D91" if camp == CHO else "#991B1B"
                font_scale = 0.25 if name in ("楚", "漢") else (0.21 if name in ("車", "包", "馬", "象") else 0.18)
                font_size = max(int(self.cell_size * font_scale), 9)
                self.canvas.create_text(
                    x, y, text=name,
                    font=("Batang", font_size, "bold"),
                    fill=fg_color
                )

    def on_resign(self):
        if not self.game_active:
            return
        if not messagebox.askyesno("기권", "정말 기권하시겠습니까? 기권패로 처리됩니다."):
            return

        if self.mode == "network" and self.sock:
            try:
                self.sock.sendall(b"RESIGN\n")
            except Exception:
                pass
            winner = HAN if self.my_camp == CHO else CHO
        else:
            winner = HAN if self.game.turn == CHO else CHO

        self.finish_game(winner, reason="기권패")

    def finish_game(self, winner, reason=""):
        self.game_active = False
        msg = f"[{winner}] 진영이 승리하였습니다!"
        if reason:
            msg = f"{reason}로 인해 {msg}"
        messagebox.showinfo("게임 종료", msg)
        if self.on_game_end:
            is_win = (winner == self.my_camp)
            self.on_game_end(is_win)
        self.root.destroy()

    def on_click(self, event):
        if not self.game_active:
            return

        if self.mode == "network" and self.game.turn != self.my_camp:
            return

        clicked = self.to_grid(event.x, event.y)
        if not clicked:
            return

        r, c = clicked
        piece = self.game.board[r][c]

        if self.selected_pos and (r, c) in self.valid_moves:
            r1, c1 = self.selected_pos
            success, res = self.game.make_move(r1, c1, r, c)
            if success:
                self.last_move = (r1, c1, r, c)
                if self.mode == "network" and self.sock:
                    try:
                        self.sock.sendall(f"{r1} {c1} {r} {c}\n".encode("utf-8"))
                    except Exception:
                        messagebox.showerror("오류", "상대방과의 통신이 끊어졌습니다.")

                self.selected_pos = None
                self.valid_moves = []
                self.draw_board()
                self.update_status()

                game_over, winner = res
                if game_over:
                    self.finish_game(winner)
                return

        if piece and piece[0] == self.game.turn:
            self.selected_pos = (r, c)
            self.valid_moves = self.game.get_valid_moves(r, c)
        else:
            self.selected_pos = None
            self.valid_moves = []

        self.draw_board()

    def receive_network_moves(self):
        sock_file = self.sock.makefile("r", encoding="utf-8")
        while self.game_active:
            try:
                line = sock_file.readline()
                if not line:
                    break
                line = line.strip()
                if line == "RESIGN":
                    # 상대방이 기권한 경우
                    winner = self.my_camp
                    self.root.after(0, self.finish_game, winner, "상대방의 기권")
                    break

                parts = line.split()
                if len(parts) == 4:
                    r1, c1, r2, c2 = map(int, parts)
                    self.root.after(0, self.apply_opponent_move, r1, c1, r2, c2)
            except Exception:
                break

    def apply_opponent_move(self, r1, c1, r2, c2):
        success, res = self.game.make_move(r1, c1, r2, c2)
        if success:
            self.last_move = (r1, c1, r2, c2)
            self.draw_board()
            self.update_status()
            game_over, winner = res
            if game_over:
                self.finish_game(winner)


# ----------------------------------------------------
# 홈 화면 (0~12급 및 0~1290점 클램핑 적용)
# ----------------------------------------------------
class JanggiHome:
    def __init__(self, root):
        self.root = root
        self.root.title("장기 홈 화면")
        self.root.geometry("380x370")
        self.root.configure(bg="#221A15")
        self.root.resizable(False, False)

        # 초기 점수 1100점 (11급)
        self.score = 1100

        self.lbl_title = tk.Label(
            self.root, text="파이썬 고화질 장기", font=("Malgun Gothic", 16, "bold"),
            bg="#221A15", fg="#F2DFC0", pady=12
        )
        self.lbl_title.pack()

        self.info_frame = tk.Frame(self.root, bg="#2C221C", highlightbackground="#7F4D1B", highlightthickness=2, padx=16, pady=8)
        self.info_frame.pack(fill=tk.X, padx=30, pady=6)

        self.rank_label = tk.Label(
            self.info_frame, text="", font=("Malgun Gothic", 15, "bold"),
            bg="#2C221C", fg="#EAB308"
        )
        self.rank_label.pack()

        self.score_label = tk.Label(
            self.info_frame, text="", font=("Malgun Gothic", 11),
            bg="#2C221C", fg="#D19C5B"
        )
        self.score_label.pack()

        self.update_rank_ui()

        btn_style = {
            "font": ("Malgun Gothic", 10, "bold"),
            "width": 28, "height": 2,
            "bg": "#C69255", "fg": "#221A15",
            "activebackground": "#DFB15B", "relief": "flat", "cursor": "hand2"
        }

        tk.Button(self.root, text="1. 한 컴퓨터로 플레이 (로컬 2인)", command=self.launch_local, **btn_style).pack(pady=4)
        tk.Button(self.root, text="2. 온라인 방 만들기 (호스트 - 초)", command=self.launch_server, **btn_style).pack(pady=4)
        tk.Button(self.root, text="3. 온라인 방 접속하기 (게스트 - 한)", command=self.launch_client, **btn_style).pack(pady=4)

    def get_rank_str(self):
        # 0급에서 12급 (점수 0 ~ 1290)
        # 앞 두 자리를 급수로 산정 (100 미만은 0급, 최대 12급)
        if self.score < 100:
            rank_num = 0
        else:
            rank_num = int(str(self.score)[:2])
        rank_num = min(12, max(0, rank_num))
        return f"{rank_num}급"

    def update_rank_ui(self):
        self.rank_label.config(text=f"내 급수: {self.get_rank_str()}")
        self.score_label.config(text=f"현재 점수: {self.score}점 (범위: 0 ~ 1290)")

    def handle_game_result(self, is_win):
        # 승리 시 10 감소, 패배 시 10 증가 (0 ~ 1290 클램핑)
        if is_win:
            self.score = max(0, self.score - 10)
            msg = f"승리하셨습니다!\n점수가 10점 감소하여 {self.score}점이 되었습니다.\n(급수: {self.get_rank_str()})"
        else:
            self.score = min(1290, self.score + 10)
            msg = f"패배하셨습니다...\n점수가 10점 증가하여 {self.score}점이 되었습니다.\n(급수: {self.get_rank_str()})"

        self.update_rank_ui()
        messagebox.showinfo("전적 반영", msg)
        self.root.deiconify()

    def launch_local(self):
        self.root.withdraw()
        game_win = tk.Toplevel(self.root)
        JanggiGUI(game_win, mode="local", on_game_end=self.handle_game_result)

    def launch_server(self):
        port = simpledialog.askinteger("방 생성", "포트 번호를 입력하세요 (기본: 9999):", initialvalue=9999)
        if not port:
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("0.0.0.0", port))
        server.listen(1)

        wait_win = tk.Toplevel(self.root)
        wait_win.title("대기 중")
        wait_win.geometry("280x100")
        tk.Label(wait_win, text=f"포트 {port}에서 대기 중...\n상대방의 접속을 기다립니다.", pady=20).pack()
        self.root.update()

        def accept_thread():
            conn, _ = server.accept()
            conn.sendall(b"ROLE:HAN\n")
            wait_win.destroy()
            self.root.withdraw()
            game_win = tk.Toplevel(self.root)
            JanggiGUI(game_win, mode="network", sock=conn, my_camp=CHO, on_game_end=self.handle_game_result)
            server.close()

        threading.Thread(target=accept_thread, daemon=True).start()

    def launch_client():
        pass

    def launch_client(self):
        ip = simpledialog.askstring("접속", "호스트 IP 주소를 입력하세요:", initialvalue="127.0.0.1")
        if not ip:
            return
        port = simpledialog.askinteger("접속", "포트 번호를 입력하세요:", initialvalue=9999)
        if not port:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip, port))
        except Exception as e:
            messagebox.showerror("접속 실패", f"서버에 접속할 수 없습니다: {e}")
            return

        role_msg = sock.recv(1024).decode().strip()
        my_camp = HAN if "HAN" in role_msg else CHO

        self.root.withdraw()
        game_win = tk.Toplevel(self.root)
        JanggiGUI(game_win, mode="network", sock=sock, my_camp=my_camp, on_game_end=self.handle_game_result)


if __name__ == "__main__":
    root = tk.Tk()
    app = JanggiHome(root)
    root.mainloop()
