import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window

# For Android Native Text-to-Speech
from plyer import tts

# ==========================================
# CONFIGURATION / EDITABLE VARIABLES 
# ==========================================
DELAYS = {
    "GAZE 1 LEFT":  10.0,
    "GAZE 2 LEFT":  35.0,
    "GAZE 1 RIGHT": 17.0,
    "GAZE 2 RIGHT": 42.0,
}

MESSAGES = {
    "GAZE 1 LEFT":  {"normal": "Gaze, Look away", "cross": "Gaze, look in"},
    "GAZE 2 LEFT":  {"normal": "Gaze, Look away", "cross": "Gaze, look in"},
    "GAZE 1 RIGHT": {"normal": "Bait middle, then stay", "cross": "Bait middle, then out"},
    "GAZE 2 RIGHT": {"normal": "Bait middle, then out", "cross": "Bait middle, then stay"}
}

# -------------------------------------------------------------------
# CUSTOM BUTTONS & COMPONENTS
# -------------------------------------------------------------------

class ImageButton(Button):
    """Custom Kivy button that can draw a cross over itself and change background colors based on state."""
    def __init__(self, is_cross=False, **kwargs):
        super().__init__(**kwargs)
        self.is_cross = is_cross
        self.is_selected = False
        self.group_has_selection = False
        self.background_normal = ''  # Allows custom background coloring
        
        # Redraw canvas when sizes change
        self.bind(size=self.update_canvas, pos=self.update_canvas)
        self.update_appearance()

    def update_appearance(self):
        if self.is_selected:
            self.background_color = (1, 0, 0, 1)  # Red Border/Fill indicator
            self.color = (1, 1, 1, 1)
        elif self.group_has_selection and not self.is_selected:
            self.background_color = (0.5, 0.5, 0.5, 0.5)  # Grayed out
            self.color = (0.7, 0.7, 0.7, 1)
        else:
            self.background_color = (1, 1, 1, 1)  # White/Default
            self.color = (0, 0, 0, 1)
            
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.after.clear()
        if self.is_cross:
            with self.canvas.after:
                Color(0, 0, 0, 0.7)  # Semi-transparent black line
                # Draw 'X' marks inside padding bounds
                Line(points=[self.x + 15, self.y + 15, self.right - 15, self.top - 15], width=2)
                Line(points=[self.right - 15, self.y + 15, self.x + 15, self.top - 15], width=2)


class GazeGroup(BoxLayout):
    """Encapsulates a Left or Right Gaze pair with selection & sequence sorting UI."""
    def __init__(self, group_id, fallback_text, has_order_buttons=False, on_order_change_callback=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = 10
        self.group_id = group_id
        self.has_order_buttons = has_order_buttons
        self.on_order_change_callback = on_order_change_callback
        self.selected_order = None
        self.current_selection = None

        # Label Left Indicator
        if "LEFT" in group_id:
            lbl_text = group_id.split()[0] + " " + group_id.split()[1]
            self.label = Label(text=lbl_text, size_hint_x=0.25, bold=True, color=(0,0,0,1))
            self.add_widget(self.label)

        # Action Buttons
        self.btn_normal = ImageButton(is_cross=False, text=fallback_text)
        self.btn_cross = ImageButton(is_cross=True, text=fallback_text)
        
        self.btn_normal.bind(on_release=lambda x: self.button_clicked(self.btn_normal))
        self.btn_cross.bind(on_release=lambda x: self.button_clicked(self.btn_cross))
        
        self.add_widget(self.btn_normal)
        self.add_widget(self.btn_cross)

        # Order Toggles (1 / 2) for Right Hand Grid
        if self.has_order_buttons:
            order_box = BoxLayout(orientation='vertical', size_hint_x=0.2, spacing=4)
            self.btn_1 = Button(text="1", bold=True, background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
            self.btn_2 = Button(text="2", bold=True, background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
            
            self.btn_1.bind(on_release=lambda x: self.order_clicked(1))
            self.btn_2.bind(on_release=lambda x: self.order_clicked(2))
            
            order_box.add_widget(self.btn_1)
            order_box.add_widget(self.btn_2)
            self.add_widget(order_box)

    def button_clicked(self, clicked_btn):
        sel_type = "normal" if clicked_btn == self.btn_normal else "cross"
        if clicked_btn.is_selected:
            self.clear_selection()
        else:
            self.current_selection = sel_type
            self.btn_normal.is_selected = (clicked_btn == self.btn_normal)
            self.btn_cross.is_selected = (clicked_btn == self.btn_cross)
            self.btn_normal.group_has_selection = True
            self.btn_cross.group_has_selection = True
            
        self.btn_normal.update_appearance()
        self.btn_cross.update_appearance()

    def order_clicked(self, number):
        if self.on_order_change_callback:
            self.on_order_change_callback(self.group_id, number)

    def set_order_selection(self, number):
        self.selected_order = number
        if not self.has_order_buttons: return
        
        if self.selected_order == 1:
            self.btn_1.background_color = (1, 0, 0, 1)  # Red highlighted
            self.btn_1.color = (1, 1, 1, 1)
            self.btn_2.background_color = (0.9, 0.9, 0.9, 1)
            self.btn_2.color = (0.5, 0.5, 0.5, 1)
        elif self.selected_order == 2:
            self.btn_1.background_color = (0.9, 0.9, 0.9, 1)
            self.btn_1.color = (0.5, 0.5, 0.5, 1)
            self.btn_2.background_color = (1, 0, 0, 1)
            self.btn_2.color = (1, 1, 1, 1)

    def clear_selection(self):
        self.current_selection = None
        self.btn_normal.is_selected = False
        self.btn_cross.is_selected = False
        self.btn_normal.group_has_selection = False
        self.btn_cross.group_has_selection = False
        self.btn_normal.update_appearance()
        self.btn_cross.update_appearance()
        if self.has_order_buttons:
            self.selected_order = None
            self.btn_1.background_color = (1, 1, 1, 1)
            self.btn_1.color = (0, 0, 0, 1)
            self.btn_2.background_color = (1, 1, 1, 1)
            self.btn_2.color = (0, 0, 0, 1)


# -------------------------------------------------------------------
# MAIN WINDOW FRAMEWORK
# -------------------------------------------------------------------

class GameOverlayAssistantApp(App):
    def build(self):
        # Setup mobile window canvas background
        Window.clearcolor = (0.96, 0.96, 0.96, 1) # #f5f5f5 equivalent
        
        self.active_matrix_choice = None
        self.matrix_buttons = {}
        
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # --- SECTION 1: GAZE MATRIX GRID ---
        grid_layout = GridLayout(cols=2, spacing=15, size_hint_y=0.45)
        
        self.groups = {
            "GAZE 1 LEFT":  GazeGroup("GAZE 1 LEFT", "G1 Left"),
            "GAZE 1 RIGHT": GazeGroup("GAZE 1 RIGHT", "G1 Right", has_order_buttons=True, on_order_change_callback=self.sync_right_side_orders),
            "GAZE 2 LEFT":  GazeGroup("GAZE 2 LEFT", "G2 Left"),
            "GAZE 2 RIGHT": GazeGroup("GAZE 2 RIGHT", "G2 Right", has_order_buttons=True, on_order_change_callback=self.sync_right_side_orders)
        }
        
        grid_layout.add_widget(self.groups["GAZE 1 LEFT"])
        grid_layout.add_widget(self.groups["GAZE 1 RIGHT"])
        grid_layout.add_widget(self.groups["GAZE 2 LEFT"])
        grid_layout.add_widget(self.groups["GAZE 2 RIGHT"])
        main_layout.add_widget(grid_layout)
        
        # --- SECTION 2: SEQUENCE EXECUTIVE CONTROLS ---
        control_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15, padding=[20, 5, 20, 5])
        btn_reset = Button(text="reset", background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
        btn_play = Button(text="play", background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
        
        btn_reset.bind(on_release=lambda x: self.reset_selections())
        btn_play.bind(on_release=lambda x: self.play_sequences())
        
        control_layout.add_widget(btn_reset)
        control_layout.add_widget(Widget()) # Dynamic Spacer
        control_layout.add_widget(btn_play)
        main_layout.add_widget(control_layout)
        
        # --- SECTION 3: TRUTH TABLE INTERACTION ---
        logic_section = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=20)
        
        left_toggle_layout = BoxLayout(orientation='vertical', spacing=6, size_hint_x=0.3)
        self.btn_flig = Button(text="F.Lig", background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
        self.btn_fice = Button(text="F.Ice", background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
        
        self.btn_flig.bind(on_release=lambda x: self.toggle_logic_state(self.btn_flig))
        self.btn_fice.bind(on_release=lambda x: self.toggle_logic_state(self.btn_fice))
        
        left_toggle_layout.add_widget(self.btn_flig)
        left_toggle_layout.add_widget(self.btn_fice)
        logic_section.add_widget(left_toggle_layout)
        
        right_matrix_layout = GridLayout(cols=2, spacing=5, size_hint_x=0.7)
        for option in ["Real", "F.Ice", "F.Lig", "Fake"]:
            btn = Button(text=option, background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
            btn.bind(on_release=lambda x, opt=option: self.matrix_choice_clicked(opt))
            right_matrix_layout.add_widget(btn)
            self.matrix_buttons[option] = btn
            
        logic_section.add_widget(right_matrix_layout)
        main_layout.add_widget(logic_section)
        
        # --- SECTION 4: REAL-TIME ANSWER READOUT ---
        answer_container = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        answer_container.add_widget(Widget(size_hint_x=0.2))
        
        self.lbl_answer = Label(text="", font_size='22sp', bold=True, color=(0,0,0,1), halign='center')
        answer_container.add_widget(self.lbl_answer)
        
        btn_clear_logic = Button(text="clear", size_hint_x=0.2, background_normal='', background_color=(1,1,1,1), color=(0,0,0,1))
        btn_clear_logic.bind(on_release=lambda x: self.reset_truth_table_only())
        answer_container.add_widget(btn_clear_logic)
        
        main_layout.add_widget(answer_container)
        return main_layout

    def toggle_logic_state(self, button):
        # Toggle background behavior acting as checkable flags
        if button.background_color == [1, 0, 0, 1]:
            button.background_color = (1, 1, 1, 1)
            button.color = (0, 0, 0, 1)
        else:
            button.background_color = (1, 0, 0, 1)
            button.color = (1, 1, 1, 1)
        self.evaluate_truth_table()

    def matrix_choice_clicked(self, choice):
        self.active_matrix_choice = choice
        for opt, btn in self.matrix_buttons.items():
            if opt == choice:
                btn.background_color = (1, 0, 0, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (1, 1, 1, 1)
                btn.color = (0, 0, 0, 1)
        self.evaluate_truth_table()

    def evaluate_truth_table(self):
        if not self.active_matrix_choice:
            self.lbl_answer.text = ""
            return
            
        state_ice = "fake" if self.btn_fice.background_color == [1, 0, 0, 1] else "real"
        state_lig = "fake" if self.btn_flig.background_color == [1, 0, 0, 1] else "real"
        
        result = ""
        col = self.active_matrix_choice.lower()
        
        if state_ice == "real" and state_lig == "real":
            if col == "real":    result = "real"
            elif col == "f.ice":  result = "fake ice"
            elif col == "f.lig":  result = "fake lightning"
            elif col == "fake":   result = "fake"
        elif state_ice == "fake" and state_lig == "real":
            if col == "real":    result = "fake ice"
            elif col == "f.ice":  result = "real"
            elif col == "f.lig":  result = "fake"
            elif col == "fake":   result = "fake lightning"
        elif state_ice == "real" and state_lig == "fake":
            if col == "real":    result = "fake lightning"
            elif col == "f.ice":  result = "fake"
            elif col == "f.lig":  result = "real"
            elif col == "fake":   result = "fake ice"
        elif state_ice == "fake" and state_lig == "fake":
            if col == "real":    result = "fake"
            elif col == "f.ice":  result = "fake lightning"
            elif col == "f.lig":  result = "fake ice"
            elif col == "fake":   result = "real"
            
        self.lbl_answer.text = result.upper()

    def sync_right_side_orders(self, calling_group, selected_number):
        other_number = 2 if selected_number == 1 else 1
        if calling_group == "GAZE 1 RIGHT":
            self.groups["GAZE 1 RIGHT"].set_order_selection(selected_number)
            self.groups["GAZE 2 RIGHT"].set_order_selection(other_number)
        else:
            self.groups["GAZE 2 RIGHT"].set_order_selection(selected_number)
            self.groups["GAZE 1 RIGHT"].set_order_selection(other_number)

    def reset_selections(self):
        for group in self.groups.values():
            group.clear_selection()

    def reset_truth_table_only(self):
        self.btn_flig.background_color = (1,1,1,1)
        self.btn_flig.color = (0,0,0,1)
        self.btn_fice.background_color = (1,1,1,1)
        self.btn_fice.color = (0,0,0,1)
        self.active_matrix_choice = None
        
        for btn in self.matrix_buttons.values():
            btn.background_color = (1, 1, 1, 1)
            btn.color = (0, 0, 0, 1)
            
        self.lbl_answer.text = ""

    def play_sequences(self):
        start_time = time.time()
        g1_right_order = self.groups["GAZE 1 RIGHT"].selected_order
        g2_right_order = self.groups["GAZE 2 RIGHT"].selected_order
        g1_right_base_delay = DELAYS["GAZE 1 RIGHT"]
        g2_right_base_delay = DELAYS["GAZE 2 RIGHT"]
        
        for group_key, group_obj in self.groups.items():
            selection = group_obj.current_selection
            if selection:
                message = MESSAGES[group_key][selection]
                if group_key == "GAZE 1 RIGHT" and g1_right_order == 2:
                    delay = g2_right_base_delay
                elif group_key == "GAZE 2 RIGHT" and g2_right_order == 1:
                    delay = g1_right_base_delay
                else:
                    delay = DELAYS[group_key]
                
                threading.Thread(
                    target=self._delayed_speech_worker, 
                    args=(start_time, delay, message), 
                    daemon=True
                ).start()

    def _delayed_speech_worker(self, start_time, delay, message):
        target_time = start_time + delay
        time_to_wait = target_time - time.time()
        if time_to_wait > 0:
            time.sleep(time_to_wait)
        try:
            # Native Engine dispatch via Plyer
            tts.speak(message)
        except Exception as e:
            print(f"TTS Notice: {e}")


if __name__ == "__main__":
    GameOverlayAssistantApp().run()
