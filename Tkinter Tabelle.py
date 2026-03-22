import json
import os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

# Hintergrundfarbe der App (helles Grau)
Window.clearcolor = get_color_from_hex('#F5F5F5')

DB_FILE = "kunden_daten.json"


class StyledButton(Button):
    def __init__(self, bg_color='#2196F3', **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)  # Transparent machen für eigene Zeichnung
        self.bg_hex = bg_color
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(rgba=get_color_from_hex(self.bg_hex))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10, ])


class KundenApp(App):
    def build(self):
        self.title = "Zahlungs-Manager"
        self.kunden = self.load_data()

        # Hauptlayout
        root = BoxLayout(orientation='vertical', padding=15, spacing=15)

        # --- Header ---
        header = Label(
            text="Kundenverwaltung",
            font_size='24sp',
            bold=True,
            size_hint_y=None,
            height=50,
            color=get_color_from_hex('#333333')
        )
        root.add_widget(header)

        # --- Eingabebereich (Card-Style) ---
        input_card = BoxLayout(orientation='vertical', size_hint_y=None, height=220, padding=15, spacing=10)
        with input_card.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            RoundedRectangle(pos=input_card.pos, size=input_card.size, radius=[15, ])
        input_card.bind(pos=self._update_rect, size=self._update_rect)

        # Eingabefelder
        self.ent_kunde = self.create_input("Name des Kunden")
        self.ent_tel = self.create_input("Telefonnummer")
        self.ent_tage = self.create_input("Zahlungsziel (Tage)", is_int=True)
        self.ent_tage.text = "14"

        input_card.add_widget(self.ent_kunde)
        input_card.add_widget(self.ent_tel)
        input_card.add_widget(self.ent_tage)

        # Hinzufügen Button
        btn_add = StyledButton(text="Kunden hinzufügen", bg_color='#4CAF50', size_hint_y=None, height=50, bold=True)
        btn_add.bind(on_press=self.add_kunde)
        input_card.add_widget(btn_add)

        root.add_widget(input_card)

        # --- Scroll-Liste ---
        self.scroll_view = ScrollView()
        self.kunden_liste = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=[0, 10])
        self.kunden_liste.bind(minimum_height=self.kunden_liste.setter('height'))
        self.scroll_view.add_widget(self.kunden_liste)

        root.add_widget(self.scroll_view)

        self.refresh_table()
        return root

    def _update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(rgba=get_color_from_hex('#FFFFFF'))
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[15, ])

    def create_input(self, hint, is_int=False):
        ti = TextInput(
            hint_text=hint,
            multiline=False,
            padding=[10, 10],
            background_normal='',
            background_color=(0.95, 0.95, 0.95, 1),
            size_hint_y=None,
            height=45
        )
        if is_int: ti.input_filter = 'int'
        return ti

    def load_data(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_data(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.kunden, f, indent=4)

    def add_kunde(self, instance):
        if self.ent_kunde.text and self.ent_tage.text:
            neuer_kunde = {
                "name": self.ent_kunde.text,
                "telefon": self.ent_tel.text,
                "datum": datetime.now().strftime("%d-%m-%Y"),
                "tage": int(self.ent_tage.text),
                "status": "Offen"
            }
            self.kunden.append(neuer_kunde)
            self.save_data()
            self.refresh_table()
            self.ent_kunde.text = ""
            self.ent_tel.text = ""
        else:
            self.show_popup("Fehler", "Bitte Name und Tage ausfüllen.")

    def refresh_table(self):
        self.kunden_liste.clear_widgets()
        heute = datetime.now().date()

        for idx, k in enumerate(self.kunden):
            erstellt = datetime.strptime(k["datum"], "%d-%m-%Y").date()
            faellig = erstellt + timedelta(days=k["tage"])

            # Status-Farbe bestimmen
            status_color = '#757575'  # Grau (Offen)
            if k["status"] == "Bezahlt":
                status_color = '#2E7D32'  # Grün
            elif faellig < heute:
                status_color = '#C62828'  # Rot
            elif (faellig - heute).days <= 3:
                status_color = '#F9A825'  # Orange

            # Card-Button Design
            card_text = f"[b]{k['name']}[/b]\n[size=14sp]Fällig: {faellig} | Tel: {k['telefon']}[/size]"
            row_btn = Button(
                text=card_text,
                markup=True,
                size_hint_y=None, height=90,
                background_normal='',
                background_color=(0, 0, 0, 0),
                color=(1, 1, 1, 1),
                halign='left',
                padding=[20, 10]
            )
            row_btn.bind(size=row_btn.setter('text_size'))  # Text-Wrapping

            with row_btn.canvas.before:
                Color(rgba=get_color_from_hex(status_color))
                RoundedRectangle(pos=row_btn.pos, size=row_btn.size, radius=[12, ])

            # Canvas Update bei Resize
            def update_btn_canvas(btn, *args, c=status_color):
                btn.canvas.before.clear()
                with btn.canvas.before:
                    Color(rgba=get_color_from_hex(c))
                    RoundedRectangle(pos=btn.pos, size=btn.size, radius=[12, ])

            row_btn.bind(pos=update_btn_canvas, size=update_btn_canvas)

            row_btn.bind(on_release=lambda btn, i=idx: self.show_options(i))
            self.kunden_liste.add_widget(row_btn)

    def show_options(self, idx):
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)

        btn_paid = StyledButton(text="Als Bezahlt markieren", bg_color='#2E7D32', height=60, size_hint_y=None)
        btn_del = StyledButton(text="Eintrag löschen", bg_color='#D32F2F', height=60, size_hint_y=None)
        btn_close = StyledButton(text="Abbrechen", bg_color='#757575', height=60, size_hint_y=None)

        popup = Popup(title='Kunden-Optionen', content=content, size_hint=(0.85, 0.5), background_color=[1, 1, 1, 1])

        def mark_paid(inst):
            self.kunden[idx]["status"] = "Bezahlt"
            self.save_data()
            self.refresh_table()
            popup.dismiss()

        def delete_k(inst):
            del self.kunden[idx]
            self.save_data()
            self.refresh_table()
            popup.dismiss()

        btn_paid.bind(on_release=mark_paid)
        btn_del.bind(on_release=delete_k)
        btn_close.bind(on_release=popup.dismiss)

        content.add_widget(btn_paid)
        content.add_widget(btn_del)
        content.add_widget(btn_close)
        popup.open()

    def show_popup(self, title, text):
        box = BoxLayout(orientation='vertical', padding=15)
        box.add_widget(Label(text=text, color=(0, 0, 0, 1)))
        btn = StyledButton(text="OK", bg_color='#2196F3', size_hint_y=None, height=50)
        box.add_widget(btn)
        popup = Popup(title=title, content=box, size_hint=(0.7, 0.3))
        btn.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    KundenApp().run()