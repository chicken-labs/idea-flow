import tkinter as tk
import random
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

GRID_SIZE = 20
CELL_SIZE = 30
NEW_IDEA_EVERY = 100

class Cell:
    def __init__(self):
        self.worldviews = {}  # {'A': strength, ...}
        self.charisma = min(max(random.gauss(5, 2), 1), 10)

    def dominant_view(self):
        if self.worldviews:
            return max(self.worldviews.items(), key=lambda x: x[1])[0]
        return None

    def influence(self, neighbor):
        for view, strength in self.worldviews.items():
            influence_strength = (strength / 10) * ((self.charisma / 10) ** 2)
            if view not in neighbor.worldviews:
                if random.random() < influence_strength:
                    neighbor.worldviews[view] = 1
            else:
                neighbor.worldviews[view] += influence_strength
        self.normalize_worldviews(neighbor)
        self.limit_worldviews(neighbor)

    def normalize_worldviews(self, neighbor):
        total = sum(neighbor.worldviews.values())
        if total > 10:
            for k in neighbor.worldviews:
                neighbor.worldviews[k] = (neighbor.worldviews[k] / total) * 10

    def limit_worldviews(self, neighbor):
        if len(neighbor.worldviews) > 3:
            top_views = sorted(neighbor.worldviews.items(), key=lambda x: x[1], reverse=True)[:3]
            neighbor.worldviews = dict(top_views)

def get_neighbors(grid, x, y):
    neighbors = []
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
            neighbors.append(grid[nx][ny])
    return neighbors

def simulate_day(grid):
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            cell = grid[x][y]
            neighbors = get_neighbors(grid, x, y)
            for neighbor in neighbors:
                cell.influence(neighbor)

def introduce_new_idea(grid, existing_views):
    new_views = [chr(i) for i in range(65, 91) if chr(i) not in existing_views]
    if not new_views:
        return
    new_view = random.choice(new_views)
    x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
    grid[x][y].worldviews[new_view] = 10
    existing_views.add(new_view)

class SimulationApp:
    def __init__(self, master):
        self.master = master
        self.canvas = tk.Canvas(master, width=GRID_SIZE*CELL_SIZE, height=GRID_SIZE*CELL_SIZE)
        self.canvas.pack()

        self.control_frame = tk.Frame(master)
        self.control_frame.pack()
        self.start_button = tk.Button(self.control_frame, text="Start", command=self.toggle)
        self.start_button.pack(side=tk.LEFT)
        self.reset_button = tk.Button(self.control_frame, text="Reset", command=self.reset)
        self.reset_button.pack(side=tk.LEFT)
        self.day_label = tk.Label(self.control_frame, text="Day: 0")
        self.day_label.pack(side=tk.LEFT)
        self.tooltip = tk.Label(self.master, text="", bg="lightyellow", relief=tk.SOLID, bd=1)

        self.chart_fig, self.chart_ax = plt.subplots(figsize=(4, 2))
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, master)
        self.chart_canvas.get_tk_widget().pack()

        self.running = False
        self.reset()

    def reset(self):
        self.grid = [[Cell() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.day = 0
        self.existing_views = set()
        introduce_new_idea(self.grid, self.existing_views)
        introduce_new_idea(self.grid, self.existing_views)
        self.running = False
        self.start_button.config(text="Start")
        self.draw_grid()
        self.day_label.config(text="Day: 0")

    def toggle(self):
        self.running = not self.running
        if self.running:
            self.start_button.config(text="Pause")
            self.step_simulation()
        else:
            self.start_button.config(text="Start")

    def step_simulation(self):
        if not self.running:
            return
        self.day += 1
        simulate_day(self.grid)
        if self.day % NEW_IDEA_EVERY == 0:
            introduce_new_idea(self.grid, self.existing_views)
        self.draw_grid()
        self.day_label.config(text=f"Day: {self.day}")
        self.master.after(100, self.step_simulation)

    def draw_grid(self):
        self.canvas.delete("all")
        view_counts = Counter()
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                cell = self.grid[x][y]
                view = cell.dominant_view()
                if view:
                    view_counts[view] += 1
                color = self.view_color(view)
                border_width = 3 if cell.charisma > 8 else 1
                rect = self.canvas.create_rectangle(
                    x * CELL_SIZE, y * CELL_SIZE,
                    (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                    fill=color, outline="black", width=border_width
                )
                strength = sum(cell.worldviews.values()) / 10
                bar_height = 5
                self.canvas.create_rectangle(
                    x * CELL_SIZE, (y + 1) * CELL_SIZE - bar_height,
                    x * CELL_SIZE + int(CELL_SIZE * strength), (y + 1) * CELL_SIZE,
                    fill="blue", outline="blue"
                )
                # Tooltip bindings
                self.canvas.tag_bind(rect, '<Enter>', lambda e, c=cell: self.show_tooltip(e, c))
                self.canvas.tag_bind(rect, '<Leave>', lambda e: self.hide_tooltip())

        # Update graph
        self.chart_ax.clear()
        if view_counts:
            items = sorted(view_counts.items())
            labels, values = zip(*items)
            self.chart_ax.bar(labels, values, color='skyblue')
            self.chart_ax.set_title("Dominant View Distribution")
            self.chart_fig.tight_layout()
        self.chart_canvas.draw()

    def show_tooltip(self, event, cell):
        tooltip_text = "\n".join(f"{k}: {v:.1f}" for k, v in cell.worldviews.items())
        self.tooltip.config(text=tooltip_text)
        self.tooltip.place(x=event.x_root - self.master.winfo_rootx() + 10,
                           y=event.y_root - self.master.winfo_rooty() + 10)

    def hide_tooltip(self):
        self.tooltip.place_forget()

    def view_color(self, view):
        if view is None:
            return "gray"
        random.seed(ord(view))
        r = random.randint(100, 255)
        g = random.randint(100, 255)
        b = random.randint(100, 255)
        return f"#{r:02x}{g:02x}{b:02x}"

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Idea Flow Simulation")
    app = SimulationApp(root)
    root.mainloop()
