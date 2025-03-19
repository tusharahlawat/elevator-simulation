import tkinter as tk
from tkinter import ttk
import time
from threading import Thread

class Lift:
    def __init__(self, lift_id, total_floors):
        self.lift_id = lift_id
        self.current_floor = 0  # Starting at floor 0
        self.direction = 'idle'  # 'up', 'down', 'idle'
        self.target_floors = []
        self.total_floors = total_floors
        self.state = 'idle'  # 'idle' or 'moving'
        self.travel_time = 0  # Will be set by the system

    def add_target(self, floor):
        if floor < 0 or floor > self.total_floors:
            return False  # Invalid floor
        if floor in self.target_floors:
            return True  # Already in targets

        if self.direction == 'up':
            inserted = False
            for i, tf in enumerate(self.target_floors):
                if tf < self.current_floor:
                    continue
                if floor < tf:
                    self.target_floors.insert(i, floor)
                    inserted = True
                    break
            if not inserted:
                self.target_floors.append(floor)
            self.target_floors.sort()
        elif self.direction == 'down':
            inserted = False
            for i, tf in enumerate(self.target_floors):
                if tf > self.current_floor:
                    continue
                if floor > tf:
                    self.target_floors.insert(i, floor)
                    inserted = True
                    break
            if not inserted:
                self.target_floors.append(floor)
            self.target_floors.sort(reverse=True)
        else:
            self.target_floors.append(floor)
            self.target_floors.sort()
        return True

    def move(self):
        if not self.target_floors:
            self.state = 'idle'
            self.direction = 'idle'
            return

        self.state = 'moving'
        next_floor = self.target_floors[0]

        if next_floor > self.current_floor:
            self.direction = 'up'
            self.current_floor += 1
        elif next_floor < self.current_floor:
            self.direction = 'down'
            self.current_floor -= 1
        else:
            self.target_floors.pop(0)
            if not self.target_floors:
                self.state = 'idle'
                self.direction = 'idle'

    def handle_internal_request(self, floor):
        return self.add_target(floor)


class LiftSystem:
    def __init__(self, total_floors, algorithm='fcfs', travel_time=1):
        self.total_floors = total_floors
        self.lifts = [Lift(1, total_floors), Lift(2, total_floors)]
        for lift in self.lifts:
            lift.travel_time = travel_time
        self.algorithm = algorithm
        self.external_requests = []
        self.travel_time = travel_time
        self.running = True

    def handle_external_request(self, floor, direction):
        if floor < 0 or floor > self.total_floors:
            return False
        if direction not in ['up', 'down']:
            return False

        if self.algorithm == 'fcfs':
            self.external_requests.append((floor, direction))
            self._process_fcfs_queue()
        elif self.algorithm == 'nearest':
            self._assign_to_nearest_lift(floor, direction)
        return True

    def _process_fcfs_queue(self):
        if not self.external_requests:
            return
        for lift in self.lifts:
            if lift.state == 'idle' and self.external_requests:
                floor, direction = self.external_requests.pop(0)
                lift.add_target(floor)
                break

    def _assign_to_nearest_lift(self, floor, direction):
        best_lift = None
        min_score = float('inf')

        for lift in self.lifts:
            score = self._calculate_score(lift, floor, direction)
            if score < min_score:
                min_score = score
                best_lift = lift
            elif score == min_score:
                if (lift.direction == direction and 
                    ((direction == 'up' and lift.current_floor <= floor) or 
                     (direction == 'down' and lift.current_floor >= floor))):
                    best_lift = lift

        if best_lift:
            best_lift.add_target(floor)

    def _calculate_score(self, lift, request_floor, request_direction):
        current_floor = lift.current_floor
        if lift.direction == 'up':
            if request_direction == 'up' and request_floor >= current_floor:
                return request_floor - current_floor
            elif request_direction == 'down' and request_floor <= current_floor:
                return (current_floor - request_floor) + 2 * (current_floor - request_floor)
            else:
                return float('inf')
        elif lift.direction == 'down':
            if request_direction == 'down' and request_floor <= current_floor:
                return current_floor - request_floor
            elif request_direction == 'up' and request_floor >= current_floor:
                return (request_floor - current_floor) + 2 * (request_floor - current_floor)
            else:
                return float('inf')
        else:
            return abs(current_floor - request_floor)

    def update(self):
        for lift in self.lifts:
            lift.move()

    def switch_algorithm(self, algorithm):
        if algorithm in ['fcfs', 'nearest']:
            self.algorithm = algorithm
            if algorithm == 'fcfs':
                self.external_requests = []

    def get_lift_status(self):
        return [
            {
                'id': lift.lift_id,
                'current_floor': lift.current_floor,
                'direction': lift.direction,
                'targets': lift.target_floors,
                'state': lift.state
            } for lift in self.lifts
        ]


class ElevatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Elevator Simulation")
        
        # Configuration
        self.total_floors = 10
        self.travel_time = 0.5
        
        # Create input frame for number of floors
        input_frame = ttk.LabelFrame(self.root, text="Building Configuration")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Label(input_frame, text="Number of Floors:").grid(row=0, column=0, padx=5, pady=5)
        self.floors_var = tk.IntVar(value=self.total_floors)
        floors_spin = tk.Spinbox(input_frame, from_=2, to=100, textvariable=self.floors_var, width=5)
        floors_spin.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(input_frame, text="Set Floors", command=self.set_floors).grid(row=0, column=2, padx=5, pady=5)
        
        # Initialize system
        self.system = LiftSystem(self.total_floors, 'nearest', self.travel_time)
        
        self.create_widgets()
        self.update_thread = Thread(target=self.run_simulation)
        self.update_thread.daemon = True
        self.update_thread.start()

    def set_floors(self):
        new_floors = self.floors_var.get()
        if new_floors < 2:
            return
        self.total_floors = new_floors
        self.system = LiftSystem(self.total_floors, self.system.algorithm, self.system.travel_time)
        self.floor_spin.config(from_=0, to=self.total_floors)
        self.internal_floor_spin.config(from_=0, to=self.total_floors)
        self.update_display()

    def create_widgets(self):
        # Control Panel
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(control_frame, text="Call Elevator:").grid(row=0, column=0, padx=5, pady=5)
        self.floor_var = tk.IntVar(value=1)
        self.floor_spin = tk.Spinbox(control_frame, from_=0, to=self.total_floors, textvariable=self.floor_var, width=5)
        self.floor_spin.grid(row=0, column=1, padx=5, pady=5)
        
        self.direction_var = tk.StringVar(value="up")
        ttk.Combobox(control_frame, textvariable=self.direction_var, values=["up", "down"], width=5).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Call", command=self.call_elevator).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Internal Request:").grid(row=1, column=0, padx=5, pady=5)
        self.lift_var = tk.IntVar(value=1)
        ttk.Combobox(control_frame, textvariable=self.lift_var, values=[1, 2], width=5).grid(row=1, column=1, padx=5, pady=5)
        self.internal_floor_var = tk.IntVar(value=1)
        self.internal_floor_spin = tk.Spinbox(control_frame, from_=0, to=self.total_floors, textvariable=self.internal_floor_var, width=5)
        self.internal_floor_spin.grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Request", command=self.internal_request).grid(row=1, column=3, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Switch to FCFS", command=lambda: self.switch_algorithm('fcfs')).grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Switch to Nearest", command=lambda: self.switch_algorithm('nearest')).grid(row=2, column=2, columnspan=2, padx=5, pady=5)

        # Status Display
        status_frame = ttk.LabelFrame(self.root, text="Elevator Status")
        status_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        self.lift1_status = tk.Label(status_frame, text="Lift 1: Floor 0, Idle", font=('Arial', 12))
        self.lift1_status.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.lift2_status = tk.Label(status_frame, text="Lift 2: Floor 0, Idle", font=('Arial', 12))
        self.lift2_status.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        # Visual Representation
        self.canvas = tk.Canvas(self.root, width=300, height=500, bg="white")
        self.canvas.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky="nsew")
        
        # Draw elevator shafts
        self.canvas.create_rectangle(50, 50, 100, 450, outline="black")
        self.canvas.create_rectangle(150, 50, 200, 450, outline="black")
        
        # Initial elevator positions
        self.lift1_rect = self.canvas.create_rectangle(55, 445, 95, 445-400/self.total_floors*0, fill="blue")
        self.lift2_rect = self.canvas.create_rectangle(155, 445, 195, 445-400/self.total_floors*0, fill="green")

    def call_elevator(self):
        floor = self.floor_var.get()
        direction = self.direction_var.get()
        if 0 <= floor <= self.total_floors:
            self.system.handle_external_request(floor, direction)

    def internal_request(self):
        lift_id = self.lift_var.get() - 1
        floor = self.internal_floor_var.get()
        if 0 <= floor <= self.total_floors:
            self.system.lifts[lift_id].handle_internal_request(floor)

    def switch_algorithm(self, algorithm):
        self.system.switch_algorithm(algorithm)

    def update_display(self):
        status = self.system.get_lift_status()
        
        # Update text status
        self.lift1_status.config(text=f"Lift 1: Floor {status[0]['current_floor']}, {status[0]['direction'].capitalize()}")
        self.lift2_status.config(text=f"Lift 2: Floor {status[1]['current_floor']}, {status[1]['direction'].capitalize()}")
        
        # Update visual positions
        floor_height = 400 / self.total_floors
        lift1_y = 445 - (status[0]['current_floor'] * floor_height)
        lift2_y = 445 - (status[1]['current_floor'] * floor_height)
        
        self.canvas.coords(self.lift1_rect, 55, lift1_y, 95, lift1_y + floor_height)
        self.canvas.coords(self.lift2_rect, 155, lift2_y, 195, lift2_y + floor_height)
        
        self.root.after(int(self.travel_time * 1000), self.update_display)

    def run_simulation(self):
        while True:
            self.system.update()
            time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x600")
    app = ElevatorGUI(root)
    app.update_display()
    root.mainloop()
