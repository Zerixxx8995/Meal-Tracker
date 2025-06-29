import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import sqlite3
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

class Meal:
    def __init__(self, name, calories, protein, date, id, notes=None):
        self.name = name
        self.calories = calories
        self.protein = protein
        self.date = date
        self.id = id
        self.notes = notes

    def to_dict(self):
        return {
            'name': self.name,
            'calories': self.calories,
            'protein': self.protein,
            'date': self.date,
            'id': self.id,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data['name'],
            calories=data['calories'],
            protein=data['protein'],
            date=data['date'],
            id=data['id'],
            notes=data['notes']
        )

class CalorieTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Calorie and Protein Tracker")
        self.root.geometry("800x600")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.meals = []
        self.db_file = 'meals_data.db'
        self._setup_database()
        self._load_data()
        self._create_gui()
        self._bind_shortcuts()
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

    def _setup_database(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    calories INTEGER,
                    protein REAL,
                    date TEXT,
                    notes TEXT
                )
            ''')

    def _load_data(self):
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('SELECT * FROM meals')
            self.meals = [Meal(row[1], row[2], row[3], row[4], row[0], row[5]) 
                         for row in cursor.fetchall()]

    def _save_data(self):
        with sqlite3.connect(self.db_file) as conn:
            conn.executemany('''
                INSERT OR REPLACE INTO meals (id, name, calories, protein, date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', [(meal.id, meal.name, meal.calories, meal.protein, meal.date, meal.notes) 
                 for meal in self.meals])

    def _create_gui(self):
        self._create_header()
        self._create_input_frame()
        self._create_treeview()
        self._create_button_frame()
        self._create_stats_frame()

    def _create_header(self):
        header_frame = ttk.Frame(self.root)
        header_frame.grid(row=0, column=0, pady=10, sticky="ew")
        ttk.Label(header_frame, text="Calorie and Protein Tracker", 
                 font=("Arial", 18, "bold")).pack()

    def _create_input_frame(self):
        input_frame = ttk.LabelFrame(self.root, text="Add New Meal")
        input_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        fields = [
            ("Meal Name:", "name_entry"),
            ("Calories:", "calories_entry"),
            ("Protein (g):", "protein_entry"),
            ("Notes:", "notes_entry")
        ]

        for i, (label_text, entry_name) in enumerate(fields):
            ttk.Label(input_frame, text=label_text).grid(row=i, column=0, padx=5, pady=5)
            entry = ttk.Entry(input_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            setattr(self, entry_name, entry)

        ttk.Button(input_frame, text="Add Meal", command=self._add_meal).grid(
            row=len(fields), column=0, columnspan=2, pady=10)

    def _create_treeview(self):
        tree_frame = ttk.Frame(self.root)
        tree_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ("ID", "Name", "Calories", "Protein", "Date", "Notes")
        self.treeview = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                    selectmode="extended")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.treeview.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.treeview.xview)
        self.treeview.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.treeview.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        column_configs = {
            "ID": {"width": 0, "stretch": False},
            "Name": {"width": 150, "minwidth": 100},
            "Calories": {"width": 100, "minwidth": 80},
            "Protein": {"width": 100, "minwidth": 80},
            "Date": {"width": 150, "minwidth": 120},
            "Notes": {"width": 200, "minwidth": 150}
        }

        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, **column_configs.get(col, {}))

    def _create_button_frame(self):
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=3, column=0, pady=10)
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=self._delete_meal).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", 
                  command=self._confirm_clear_all).pack(side=tk.LEFT, padx=5)

    def _create_stats_frame(self):
        stats_frame = ttk.LabelFrame(self.root, text="Statistics")
        stats_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(pady=5)
        self._update_statistics()

    def _bind_shortcuts(self):
        entries = [self.name_entry, self.calories_entry, self.protein_entry, self.notes_entry]
        for i, entry in enumerate(entries[:-1]):
            entry.bind("<Return>", lambda e, next_entry=entries[i+1]: next_entry.focus())
        entries[-1].bind("<Return>", lambda e: self._add_meal())

    def _validate_input(self, name, calories, protein):
        if not name:
            messagebox.showerror("Error", "Please enter a meal name.")
            return False

        try:
            calories = float(calories)
            protein = float(protein)
            if calories < 0 or protein < 0:
                raise ValueError
            return True
        except ValueError:
            messagebox.showerror("Error", "Please enter valid positive numbers for calories and protein.")
            return False

    def _add_meal(self):
        name = self.name_entry.get().strip()
        calories = self.calories_entry.get().strip()
        protein = self.protein_entry.get().strip()
        notes = self.notes_entry.get().strip()

        if not self._validate_input(name, calories, protein):
            return

        meal = Meal(
            name=name,
            calories=float(calories),
            protein=float(protein),
            date=str(datetime.date.today()),
            id=str(len(self.meals) + 1),
            notes=notes
        )

        self.meals.append(meal)
        self._save_data()
        self._update_statistics()
        self._refresh_treeview()
        self._clear_entries()

    def _clear_entries(self):
        for entry in (self.name_entry, self.calories_entry, self.protein_entry, self.notes_entry):
            entry.delete(0, tk.END)
        self.name_entry.focus()

    def _confirm_clear_all(self):
        if messagebox.askyesno("Confirm Clear All", 
                              "Are you sure you want to clear all meal data? This action cannot be undone."):
            self._clear_all()

    def _clear_all(self):
        self.meals.clear()
        self._save_data()
        self._update_statistics()
        self._refresh_treeview()

    def _delete_meal(self):
        selected_items = self.treeview.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a meal to delete.")
            return

        meal_ids = [self.treeview.item(item)["values"][0] for item in selected_items]
        self.meals = [meal for meal in self.meals if meal.id not in meal_ids]
        self._save_data()
        self._refresh_treeview()
        self._update_statistics()

    def _refresh_treeview(self):
        for item in self.treeview.get_children():
            self.treeview.delete(item)

        for meal in self.meals:
            self.treeview.insert("", "end", values=(
                meal.id, meal.name, meal.calories, meal.protein, meal.date, meal.notes))

    def _update_statistics(self):
        meal_stats = {}
        for meal in self.meals:
            if meal.date not in meal_stats:
                meal_stats[meal.date] = {'calories': 0, 'protein': 0}
            meal_stats[meal.date]['calories'] += meal.calories
            meal_stats[meal.date]['protein'] += meal.protein

        if meal_stats:
            self._plot_statistics(meal_stats)

    def _plot_statistics(self, meal_stats):
        dates = list(meal_stats.keys())
        calories = [meal_stats[date]['calories'] for date in dates]
        protein = [meal_stats[date]['protein'] for date in dates]

        fig, ax = plt.subplots(figsize=(10, 6))
        width = 0.4
        x = range(len(dates))

        ax.bar([p - width/2 for p in x], calories, width, label='Calories', color='blue')
        ax.bar([p + width/2 for p in x], protein, width, label='Protein (g)', color='orange')

        ax.set_xlabel('Date')
        ax.set_ylabel('Amount')
        ax.set_title('Calories and Protein per Day')
        ax.set_xticks(x)
        ax.set_xticklabels(dates, rotation=45, ha="right")
        ax.legend()

        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = CalorieTrackerApp(root)
    root.mainloop()