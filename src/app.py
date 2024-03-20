from wsgiref.util import request_uri
import pyxel
from utils import *
import time
from copy import deepcopy

class App:
    def __init__(self):
        """ゲームの状態をリセット"""
        self.FPS = 60
        self.number_of_times_played = 0
        self.game_width = 120
        self.game_height = 160
        self.width = 220
        self.height = 160
        self.initial_x = 100 # テトリミノが落ちてくるx座標
        self.initial_y = 0 # テトリミノが落ちてくるy座標
        self.hold_frame_size = 40
        self.cell_size = 10
        self.game_field = [[0 for _ in range(0, self.game_width, self.cell_size)] for _ in range(0, self.game_height, self.cell_size)]
        self.drop_speed = 45
        self.drop_counter = 0
        self.hard_droped = False
        self.held_tetrimino = None  # ホールド中のテトリミノを保持
        self.hold_use_possible = False  # ホールド機能が現在の落下で使用されたか
        self.hold_count = 0 # ホールドした回数
        self.tetrimino_touched_bottom = False
        self.frame_count = 0
        self.frame_delay = 10  # テトリミノが固定されるまでのフレーム数
        self.tetriminos = []  # 画面上のテトリミノを保持するリスト
        self.recent_tetriminos = []
        self.next_tetriminos = [self.create_new_tetrimino() for _ in range(7)] # 最初のテトリミノ + 6つの予測されたテトリミノ
        self.tetrimino = self.create_new_tetrimino() # self.tetrimino が今のテトリミノ
        self.order = ["1st", "2nd", "3rd", "4th", "5th", "6th"]
        self.best_score = 0
        self.score = 0
        self.before_score = 0
        self.start_time = time.time()
        self.state = "menu" # "menu", "play", "game_over"
        self.establishment_state = "playing" # "playing", "setting"
        self.sound_on = True
        self.drop_speed_select = [45, 40, 35] # 3つの難易度
        self.level_to_display = ["Easy", "Normal", "Difficult"]
        self.selected_speed_index = 1
        self.music_number = 0
        self.music_number_select = [0, 1] # 2つの曲番号
        self.selected_music_index = 0
        self.now_music_number = "first"
        self.music_name_to_display = ["Gameboy Music - Tetris Music A", "None"] # 曲名
        self.select_music_name = self.music_name_to_display[self.selected_music_index]
        self.now_scale = 3
        self.lock_delay = 25
        self.prev_state = "menu"
    
    def run(self):
        pyxel.init(self.width, self.height, title = "テトリス", display_scale= self.now_scale)
        pyxel.load("asset/resource.pyxres")
        pyxel.run(self.update, self.draw)
        pyxel.stop()
        
    def init(self):
        self.game_field = [[0 for _ in range(0, self.game_width, self.cell_size)] for _ in range(0, self.game_height, self.cell_size)]
        self.drop_speed = 45
        self.drop_counter = 0
        self.hard_droped = False
        self.held_tetrimino = None  # ホールド中のテトリミノを保持
        self.hold_use_possible = False
        self.hold_count = 0
        self.score = 0
        self.tetrimino_touched_bottom = False
        self.frame_count = 0
        self.tetriminos = []  # 画面上のテトリミノを保持するリスト
        self.recent_tetriminos = []
        self.next_tetriminos = [self.create_new_tetrimino() for _ in range(7)] # 最初のテトリミノ + 6つの予測されたテトリミノ
        self.tetrimino = self.create_new_tetrimino()
    
    def reset_game(self):
        """ゲームの状態をリセット"""
        self.init()
        self.prev_state = "menu"
        self.state = "menu"

    def create_new_tetrimino(self):
        available_tetriminos = list(TETROMINOES.keys())
        
        # 直近三回のテトリミノを除外して選択肢を絞る
        if len(self.recent_tetriminos) < 1:
            # 利用可能なテトリミノからランダムに選択
            letter = str(random.choice(available_tetriminos))
            shape = TETROMINOES[letter]
            color = TETROMINOES_COLORS[letter]
            # 選択したテトリミノを履歴に追加
            self.recent_tetriminos.append(letter)
            return Tetrimino(shape, 100, color)
        
        for recent in self.recent_tetriminos:
            if recent in available_tetriminos:
                available_tetriminos.remove(recent)
        
        # 利用可能なテトリミノからランダムに選択
        letter = str(random.choice(available_tetriminos))
        shape = TETROMINOES[letter]
        color = TETROMINOES_COLORS[letter]
        
        # 選択したテトリミノを履歴に追加
        self.recent_tetriminos.append(letter)
        # 履歴が3を超えたら古いものから削除
        if len(self.recent_tetriminos) > 3:
            self.recent_tetriminos.pop(0)
        return Tetrimino(shape, 100, color)
    
    def update(self):
        if self.state == "menu":
            self.update_start()
        elif self.state == "select_music":
            self.select_music()
        elif self.state == "play":
            self.update_play()
        elif self.state == "game_over":
            # QキーとRキーを同時に押すとゲームをリスタート
            if pyxel.btn(pyxel.KEY_Q) and pyxel.btn(pyxel.KEY_R):
                self.reset_game()
        elif self.state == "howto":
            if pyxel.btnp(pyxel.KEY_H):
                self.state = self.prev_state
            elif pyxel.btn(pyxel.KEY_Q) and pyxel.btn(pyxel.KEY_R):
                self.state = "play"
                
    
    def sound_replace_on_off(self):
        # 音のon/offを切り替える
        if pyxel.btnp(pyxel.KEY_N):
            self.sound_on = not self.sound_on
    
    def update_start(self):
        # 難易度の選択
        if pyxel.btnp(pyxel.KEY_UP):
            self.selected_speed_index += 1
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected_speed_index -= 1
        if self.selected_speed_index >= 2:
            self.selected_speed_index = 2
        if self.selected_speed_index <= 0:
            self.selected_speed_index = 0
        # スピードの設定をする
        self.speed = self.drop_speed_select[self.selected_speed_index]
        self.speed_level = self.level_to_display[self.selected_speed_index]
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.state = "select_music"
            
        if pyxel.btnp(pyxel.KEY_H):
            self.prev_state = self.state
            self.state = "howto"
    
    def select_music(self):
        # 曲の選択
        if pyxel.btnp(pyxel.KEY_UP):
            self.selected_music_index += 1
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected_music_index -= 1
        if self.selected_music_index >= 1:
            self.selected_music_index = 1
        if self.selected_music_index <= 0:
            self.selected_music_index = 0
        # 曲名や、曲の番号の設定をする
        self.music_number = self.music_number_select[self.selected_music_index]
        self.select_music_name = self.music_name_to_display[self.selected_music_index]
        if not self.now_music_number == self.music_number and not self.music_number == 1:
            pyxel.playm(self.music_number, loop = True)
        elif self.now_music_number == "first":
            pyxel.playm(self.music_number, loop = True)
        elif self.music_number == 1:
            pyxel.stop()
        self.now_music_number = self.music_number
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.state = "play"
            self.tetrimino = self.create_new_tetrimino()
            
        if pyxel.btnp(pyxel.KEY_H):
            self.prev_state = self.state
            self.state = "howto"
    
    def draw(self):
        if  self.state == "menu":
            # メニュー画面
            pyxel.cls(0)
            title = "TETRIS"
            pyxel.text(self.width // 2 - len(title) * 2, 38, title, pyxel.COLOR_RED)
            guide_next = "Press SPACE to start"
            pyxel.text(self.width // 2 - len(guide_next) * 2, 56, guide_next, pyxel.COLOR_WHITE)
            guide_level = "Select level with arrow key"
            pyxel.text(self.width // 2 - len(guide_level) * 2, 70, guide_level, pyxel.COLOR_LIME)
            pyxel.text(172, 69, "^", pyxel.COLOR_LIME)
            pyxel.text(172, 71, "|", pyxel.COLOR_LIME)
            pyxel.text(180, 72, "v", pyxel.COLOR_LIME)
            pyxel.text(180, 69, "|", pyxel.COLOR_LIME)
            
            level_text = f"Level: {self.speed_level}"
            pyxel.text(self.width // 2 - len(level_text) * 2, 90, level_text, pyxel.COLOR_YELLOW)
            guide_howto = "Press H key to see how to play"
            pyxel.text(self.width // 2 - len(guide_howto) * 2, 110, guide_howto, pyxel.COLOR_WHITE)
            
        elif self.state == "select_music":
            """曲の選択画面"""
            pyxel.cls(0)
            guide_music = "Select music with arrow key"
            pyxel.text(self.width // 2 - len(guide_music) * 2, 38, guide_music, pyxel.COLOR_WHITE)
            pyxel.text(170, 37, "^", pyxel.COLOR_WHITE)
            pyxel.text(170, 39, "|", pyxel.COLOR_WHITE)
            pyxel.text(178, 40, "v", pyxel.COLOR_WHITE)
            pyxel.text(178, 37, "|", pyxel.COLOR_WHITE)
            
            if not self.music_number == 1:
                pyxel.text(40, 70, "If you don't want to hear the sound,", pyxel.COLOR_ORANGE)
                pyxel.text(67, 80, "press the up arrow key", pyxel.COLOR_ORANGE)
            if self.music_number == 0:
                music_name = self.select_music_name
                pyxel.text(self.width // 2 - len(music_name) * 2, 60, music_name, pyxel.COLOR_ORANGE)
            elif self.music_number == 1:
                under_development = "Under development"
                guide_under_development = "Please wait until completion"
                pyxel.text(self.width // 2 - len(under_development) * 2, 60, under_development, pyxel.COLOR_ORANGE)
                pyxel.text(self.width // 2 - len(guide_under_development) * 2, 70, guide_under_development, pyxel.COLOR_ORANGE)
            
            start_colors = [pyxel.COLOR_RED, pyxel.COLOR_BLACK]
            guide_start = "Press SPACE to start"
            pyxel.text(self.width//2 - len(guide_start) * 2, 98, guide_start, pyxel.frame_count*3//self.FPS % 2)

        elif self.state == "play":
            """ゲームの状態が "play" のときだけ実行する"""
            pyxel.cls(0)
            pyxel.rect(self.width - 60, 0, 60, self.height, 7)
            pyxel.rectb(0, 0, 40, 40, 7)
            pyxel.line(39, 0, 39, self.height, 7)
            self.draw_board()
            self.draw_tetrimino(self.tetrimino)
            self.draw_held_tetrimino()
            # スコアとプレイ時間と選択されたレベルの描画
            self.draw_score_and_time_and_speed_info()
            self.draw_next_tetriminos()
            self.draw_next_tetoriminos_order()
            
        elif self.state == "game_over":
            """ゲームオーバー時の画面表示"""
            pyxel.cls(0)
            pyxel.text(self.width // 2 - 20, self.height // 2 - 24, "Game Over!", pyxel.COLOR_RED)
            pyxel.text(self.width // 2 - 40, self.height // 2 - 10, "Press Q+R Restart",pyxel.COLOR_WHITE)
            pyxel.text(self.width // 2 - 40, self.height // 2 + 4, "Your score:" + str(self.score), pyxel.COLOR_ORANGE)
            pyxel.text(self.width // 2 - 40, self.height // 2 + 18, "Your best score:" + str(self.best_score), pyxel.COLOR_LIGHT_BLUE)

        elif self.state == "howto":
            """遊び方の説明画面"""
            pyxel.cls(0)
            h = 30
            pyxel.text(20, h - 10, "How to play", pyxel.COLOR_RED)
            pyxel.line(20, h, 100, h, pyxel.COLOR_RED)
            pyxel.text(30, h + 14, "-  Arrow keys to move",pyxel.COLOR_WHITE)
            pyxel.text(30, h + 14 * 2, "-  Space key to hard drop", pyxel.COLOR_WHITE)
            pyxel.text(30, h + 14 * 3, "-  N key to hold/keep tetrimino", pyxel.COLOR_WHITE)
            pyxel.text(30, h + 14 * 4, "-  RShift key to rotate right", pyxel.COLOR_WHITE)
            pyxel.text(30, h + 14 * 5, "-  / key to rotate left", pyxel.COLOR_WHITE)
            pyxel.text(30, h + 14 * 6, "-  Press Q+R to restart", pyxel.COLOR_WHITE)
            
            guide = "Press H key to go back"
            guide_colors = [pyxel.COLOR_YELLOW, pyxel.COLOR_BLACK]
            pyxel.text(self.width - len(guide) * 4 - 40, self.height - 20, guide, pyxel.frame_count*3//self.FPS % 2)
            
    def draw_next_tetriminos(self):
        # 次の6つのテトリミノを画面の右側に描画
        for i, tetorimino in enumerate(self.next_tetriminos):
            x_start = self.width - 35 # テトリミノを表示するx座標の開始位置
            y_start = 45 + (i * 20) # テトリミノを表示するy座標の開始位置
            for y, row in enumerate(tetorimino.shape):
                for x, cell in enumerate(row):
                    if cell:
                        # テトリミノのセルを描画
                        pyxel.rect(x_start + x * 5, y_start + y * 5, 5, 5, tetorimino.color) # 小さめのセルで描画
    
    def draw_next_tetoriminos_order(self):
        default_y = 45
        for i in range(6):
            now_order = self.order[i]
            text = now_order
            if i == 0:
                text = "Next"
            y = default_y + 20 * i
            pyxel.text(165, y, text, pyxel.COLOR_BLACK)
    
    def draw_held_tetrimino(self):
        if not self.held_tetrimino == None:
            # ホールドされたテトリミノの形状データ
            shape = self.held_tetrimino.shape

            # テトリミノを描画する基準点（左上の40x40の枠の中央に配置するための計算）
            base_x = 20 - (len(shape[0]) * 2)  # 横幅に応じて中央揃え
            base_y = 20 - (len(shape) * 2)     # 縦幅に応じて中央揃え

            # テトリミノのセルごとに描画
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:  # セルがテトリミノの一部である場合に描画
                        pyxel.rect(base_x + x * 4, base_y + y * 4, 4, 4, self.held_tetrimino.color)
    
    def draw_board(self):
        for y, row in enumerate(self.game_field):
            for x, cell in enumerate(row):
                # 固定されたテトリミノを表示
                pyxel.rect(x*self.cell_size + 40, y*self.cell_size, self.cell_size, self.cell_size, cell)
    
    def is_game_over(self):
        """ゲームオーバー判定"""
        # テトリミノの出現場所が埋まっているかチェック
        for x in range(len(self.game_field[0])):
            if self.game_field[0][x]:
                self.state = "game_over"
                return True
        return False
    
    def update_play(self):
        
        if self.is_game_over():
            if self.best_score < self.score:
                self.best_score = self.score
        else:
            # pyxel.stop()
            pass
        
        # 遊び方の説明画面に移動
        if pyxel.btnp(pyxel.KEY_H):
            self.prev_state = self.state
            self.state = "howto"
        
        # テトリミノの下矢印キーとスペースキーの落下処理
        self.drop_counter += 1
        if pyxel.btn(pyxel.KEY_DOWN):
            self.drop_speed /= 2 
        elif pyxel.btnp(pyxel.KEY_SPACE):
            self.hard_drop_tetrimino()
        else:
            self.drop_speed = self.speed
        
        # Nキーのホールド処理
        if pyxel.btnp(pyxel.KEY_N):
            self.hold_tetrimino()
        
        # テトリミノの自動落下処理
        self.drop_counter += 1
        if self.drop_counter > self.drop_speed:
            if not self.check_collision(self.tetrimino, "down"):
                self.move_tetrimino(self.tetrimino, "down")
            else:
                # 衝突があった場合、テトリミノを固定して新しいテトリミノを生成
                # この部分はゲームのロジックに応じて実装
                pass
            self.drop_counter = 0

        # テトリミノを左に移動
        if pyxel.btnp(pyxel.KEY_LEFT):
            if not self.check_collision(self.tetrimino, "left"):
                self.move_tetrimino(self.tetrimino, "left")
        # テトリミノを右に移動
        if pyxel.btnp(pyxel.KEY_RIGHT):
            if not self.check_collision(self.tetrimino, "right"):
                self.move_tetrimino(self.tetrimino, "right")
        # テトリミノを右回転
        if pyxel.btnp(pyxel.KEY_RSHIFT):
            if not self.check_collision(self.tetrimino, "rotate"):
                self.rotate_tetrimino(self.tetrimino, "right")
        # テトリミノを左回転
        if pyxel.btnp(pyxel.KEY_SLASH):
            if not self.check_collision(self.tetrimino, "rotate"):
                self.rotate_tetrimino(self.tetrimino, "left")
        
        # 設定画面と音のONとOFFの設定
        self.sound_replace_on_off()

        # テトリミノが床に達した時の確認
        if self.check_collision(self.tetrimino,"down"):
            self.update_game_field()
            
        
        self.check_and_clear_rows(self.game_field)
        
    def update_game_field(self):
        # この時点でのゲームフィールドの分身をつくる
        self.game_field_copy = deepcopy(self.game_field)
        self.place_tetrimino(self.tetrimino, self.game_field_copy)
        if self.hard_droped == True and not self.check_and_clear_rows(self.game_field_copy):
            self.place_tetrimino(self.tetrimino, self.game_field)
            self.hold_count = 0
            self.tetrimino = self.next_tetriminos[0]
            self.next_tetriminos.pop(0)
            self.next_tetriminos.append(self.create_new_tetrimino())
            self.tetrimino_touched_bottom = False
            self.hard_droped = False
            return
        
        if self.tetrimino_touched_bottom == False:
            self.tetrimino_touched_bottom = True
            self.time_locked = 0
        if self.tetrimino_touched_bottom:
            self.time_locked += 1

            if self.time_locked > self.lock_delay:
                self.place_tetrimino(self.tetrimino, self.game_field)
                self.tetrimino = self.next_tetriminos[0]
                self.next_tetriminos.pop(0)
                self.next_tetriminos.append(self.create_new_tetrimino())
                self.tetrimino_touched_bottom = False
                self.hold_use_possible = False
                self.hold_count = 0
    
    
    def draw_score_and_time_and_speed_info(self):
        # 現在のプレイ時間を計算
        current_time = time.time()
        play_time = int(current_time - self.start_time)
        # スピードの設定をする
        self.speed_level = self.level_to_display[self.selected_speed_index]
        # スコアとプレイ時間と選択されたレベルを右サイドに表示
        pyxel.text(161, 5, f"Speed Level:", pyxel.COLOR_YELLOW)
        pyxel.text(161, 15,f"{self.speed_level}", pyxel.COLOR_PINK)
        pyxel.text(161, 25, f"Score: {self.score}", pyxel.COLOR_CYAN)
        pyxel.text(161, 35, f"Time: {play_time} sec", pyxel.COLOR_LIME)
        
    

    def draw_tetrimino(self, tetrimino):
        for y, row in enumerate(tetrimino.shape):
            for x, cell in enumerate(row):
                if cell:
                    screen_x = tetrimino.x + x
                    screen_y = tetrimino.y + y
                    pyxel.rect((tetrimino.x + x *10 + 40), (tetrimino.y + y * 10), 10, 10, tetrimino.color)


    def check_collision(self, tetrimino, direction, rotated_shape=None):
        self.collided = False
        future_x = tetrimino.x //10
        future_y = tetrimino.y //10
        shape_to_check = rotated_shape if rotated_shape is not None else tetrimino.shape

        if direction == "down":
            future_y += 1
        elif direction == "left":
            future_x -= 1
        elif direction == "right":
            future_x += 1

        for y, row in enumerate(shape_to_check):
            for x, cell in enumerate(row):
                if cell == 1:
                    new_x = future_x + x
                    new_y = future_y + y
                    if new_x < 0 or new_x >= self.game_width//10 or new_y >= self.game_height//10 or self.game_field[new_y][new_x]:
                        self.collided = True
                        return True
                    if self.game_field[new_y][new_x]:  # ほかのテトリミノに衝突
                        #self.collided = True
                        return True
                    else:
                        pass
        
        return False
    
    def hard_drop_tetrimino(self):
        """テトリミノを即座に落とす"""
        while not self.check_collision(self.tetrimino, "down", self.tetrimino.shape):
            # 衝突するまでテトリミノを1マスずつ下に移動
            self.tetrimino.y += 1
        self.hard_droped = True
    
    def move_tetrimino(self, tetrimino, direction):
        if direction == "left":
            tetrimino.x -= 10  # X座標を減らして左に移動
        elif direction == "right":
            tetrimino.x += 10  # X座標を増やして右に移動
        elif direction == "down":
            tetrimino.y += 10  # Y座標を増やして下に移動
    
    def rotate_tetrimino(self, tetrimino, direction):
        """ テトリミノを回転させる """
        if direction == "right":
            # 右回転 (時計回り)
            rotated_shape = list(zip(*tetrimino.shape[::-1]))
        elif direction == "left":
            # 左回転 (反時計回り)
            rotated_shape = list(zip(*tetrimino.shape))[::-1]
        
        # 回転後の衝突をチェック
        if not self.check_collision(tetrimino, None, rotated_shape):
            tetrimino.shape = rotated_shape
    
    def hold_tetrimino(self):
        if self.tetrimino is None:
            return
        if self.hold_count > 0:
            return
        if not self.hold_use_possible:  # ホールド機能が未使用の場合のみ実行
            if self.held_tetrimino == None:
                print(self.hold_use_possible)
                # 初めてホールドする場合、現在のテトリミノをホールドし、新しいテトリミノを生成
                self.held_tetrimino, self.tetrimino = self.tetrimino, self.next_tetriminos[0]
                self.next_tetriminos.pop(0)  # 次のテトリミノをリストから削除
                # self.tetrimino = self.create_new_tetrimino()
                self.hold_count += 1
                self.hold_use_possible = True  # ホールド機能を使用済みにする
            else:
                self.tetrimino, self.held_tetrimino = self.held_tetrimino, self.tetrimino
                self.tetrimino.x = 50
                self.tetrimino.y = 0
                self.hold_count += 1
        else:
            # 既にホールド中のテトリミノがある場合、それと現在のテトリミノを交換
            self.tetrimino, self.held_tetrimino = self.held_tetrimino, self.tetrimino
            self.hold_count += 1
        
    
    def check_and_clear_rows(self, game_field: list):
        # 埋まった行を探す
        rows_to_clear = []
        clear = False
        for y, row in enumerate(game_field):
            if all(cell for cell in row):
                clear = True
                rows_to_clear.append(y)
        
        for y in reversed(rows_to_clear):
            # 埋まった行を削除し、上の行を下にずらす
            del game_field[y]
            game_field.insert(0, [0 for _ in range(self.game_width // 10)])
            # スコアを更新する
            self.score += 150
            
        return clear

        
    def place_tetrimino(self,tetrimino, game_field: list):
        """テトリミノをゲームフィールドに固定"""
        for y, row in enumerate(tetrimino.shape):
            for x, cell in enumerate(row):
                if  cell == 1:
                    game_field[(tetrimino.y//10 + y)][(tetrimino.x//10 + x)] = tetrimino.color
    
    


if __name__ == "__main__":
    app = App()
    app.run()  