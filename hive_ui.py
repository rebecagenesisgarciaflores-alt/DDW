import os
import json
import subprocess
import threading
from nicegui import ui

# Paths
HIVE_HOME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hive_state")
BLACKBOARD = os.path.join(HIVE_HOME, "HIVE_CONTEXT.md")
QUOTA_FILE = os.path.join(HIVE_HOME, "quota_usage.json")

# State
class HiveState:
    def __init__(self):
        self.blackboard_content = ""
        self.blackboard_mtime = 0
        self.worker_stats = {}
        self.is_dispatching = False
        self.current_goal = ""
        self.skip_exhausted = True
        self.review_plan = False
        self.active_workers = {str(i): True for i in range(5)} # All active by default

state = HiveState()
worker_ui_elements = {}

def load_data():
    if os.path.exists(BLACKBOARD):
        mtime = os.path.getmtime(BLACKBOARD)
        if mtime > state.blackboard_mtime:
            try:
                with open(BLACKBOARD, "r", encoding="utf-8") as f:
                    state.blackboard_content = f.read()
                state.blackboard_mtime = mtime
            except:
                pass
    else:
        state.blackboard_content = "# Welcome to Gemini Hive\nNo active goals yet."

    if os.path.exists(QUOTA_FILE):
        try:
            with open(QUOTA_FILE, "r") as f:
                state.worker_stats = json.load(f)
        except:
            pass
    else:
        state.worker_stats = {str(i): {"requests": 0, "exhausted": False} for i in range(5)}

async def dispatch_hive():
    if not state.current_goal.strip():
        ui.notify("Please enter a goal first!", type='warning')
        return
    
    # Calculate selected workers
    selected_ids = [i for i, active in state.active_workers.items() if active]
    if not selected_ids:
        ui.notify("Please select at least one worker!", type='warning')
        return

    state.is_dispatching = True
    ui.notify(f"Dispatching Hive to {len(selected_ids)} workers...", color='primary')
    
    def run_manager():
        try:
            cmd = ["python", "hive_manager.py"]
            if state.skip_exhausted:
                cmd.append("--skip-exhausted")
            if state.review_plan:
                cmd.append("--review")
            
            cmd.append(f"--workers={','.join(selected_ids)}")
            cmd.append(state.current_goal)
            
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"Dispatch Error: {e}")
        finally:
            state.is_dispatching = False

    threading.Thread(target=run_manager, daemon=True).start()

# --- UI Layout ---

ui.query('body').style('background-color: #0d1117; color: #e6edf3;')

with ui.header().classes('items-center justify-between bg-slate-900 border-b border-slate-800 px-8 py-4'):
    ui.label('GEMINI HIVE MIND').classes('text-2xl font-bold tracking-tighter text-blue-400')
    with ui.row().classes('items-center gap-6'):
        ui.button('RESET QUOTA', on_click=lambda: subprocess.run(['python', 'hive_quota.py', '--reset'])).props('flat color=red-400').classes('text-xs font-bold')
        ui.switch('Review Plan').bind_value(state, 'review_plan').classes('text-slate-400 text-xs font-bold')
        ui.switch('Auto-Skip').bind_value(state, 'skip_exhausted').classes('text-slate-400 text-xs font-bold')
        with ui.row().classes('items-center gap-2'):
            ui.label('SYSTEM:').classes('text-slate-500 text-xs uppercase tracking-widest')
            ui.badge('ONLINE', color='green').props('outline')

with ui.column().classes('w-full p-8 max-w-7xl mx-auto gap-8'):
    
    # Fleet Health Summary
    with ui.row().classes('w-full gap-4'):
        with ui.card().classes('grow bg-slate-800/40 border border-slate-700 p-4 rounded-xl items-center justify-center'):
            active_count = sum(1 for stats in state.worker_stats.values() if not stats.get('exhausted', False))
            ui.label(f'{active_count}/5 WORKERS READY').classes('text-blue-400 font-black text-xs tracking-widest')
        with ui.card().classes('grow bg-slate-800/40 border border-slate-700 p-4 rounded-xl items-center justify-center'):
            exhausted_count = sum(1 for stats in state.worker_stats.values() if stats.get('exhausted', False))
            ui.label(f'{exhausted_count} QUOTA LIMITS HIT').classes('text-red-400 font-black text-xs tracking-widest')
        with ui.card().classes('grow bg-slate-800/40 border border-slate-700 p-4 rounded-xl items-center justify-center'):
            ui.label('AUTO-FAILOVER ENABLED').classes('text-green-400 font-black text-xs tracking-widest')

    # Action Bar
    with ui.card().classes('w-full bg-slate-800/50 border border-slate-700 p-6 rounded-2xl shadow-xl'):
        with ui.row().classes('w-full items-center gap-4'):
            ui.input(placeholder='Enter new Hive Goal here...', 
                    on_change=lambda e: setattr(state, 'current_goal', e.value)).classes('grow bg-slate-900 rounded-lg')
            ui.button('DISPATCH', on_click=dispatch_hive).props('flat color=blue-500').classes('px-8 font-bold rounded-lg')
            ui.spinner(size='md').bind_visibility_from(state, 'is_dispatching')

    with ui.row().classes('w-full gap-8 no-wrap'):
        
        # Left Panel: Blackboard
        with ui.column().classes('w-2/3 gap-4'):
            ui.label('LIVE BLACKBOARD').classes('text-slate-500 text-xs font-bold uppercase tracking-widest ml-2')
            with ui.card().classes('w-full bg-slate-900 border border-slate-800 p-8 rounded-2xl min-h-[600px] max-h-[800px] overflow-auto'):
                ui.markdown().bind_content_from(state, 'blackboard_content')
        
        # Right Panel: Workers
        with ui.column().classes('w-1/3 gap-4'):
            ui.label('WORKER FLEET MANAGEMENT').classes('text-slate-500 text-xs font-bold uppercase tracking-widest ml-2')
            
            for i in range(5):
                with ui.card().classes('w-full bg-slate-800/30 border border-slate-800 p-5 rounded-xl transition-all'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.column().classes('gap-0'):
                            ui.label(f'Worker {i}').classes('font-bold text-slate-200 text-lg')
                            health_label = ui.label('HEALTHY').classes('text-[10px] font-black tracking-tighter')
                            worker_ui_elements[f'health_{i}'] = health_label
                        
                        # Selection Dropdown (as requested)
                        sel = ui.select({True: 'ENABLED', False: 'DISABLED'}, value=True, 
                                  on_change=lambda e, idx=str(i): state.active_workers.update({idx: e.value})).props('dense flat options-dense').classes('text-xs font-bold')
                        sel.style('width: 100px; color: #60a5fa;')
                        
                        status_icon = ui.icon('circle', size='sm')
                        worker_ui_elements[f'icon_{i}'] = status_icon

                    with ui.column().classes('w-full gap-1 mt-4'):
                        with ui.row().classes('w-full justify-between items-end'):
                            ui.label('Quota Usage').classes('text-[10px] text-slate-500 uppercase font-bold')
                            req_label = ui.label('0/50').classes('text-xs font-mono text-blue-400')
                            worker_ui_elements[f'label_{i}'] = req_label
                        
                        progress = ui.linear_progress(value=0, show_value=False).classes('w-full h-2 rounded-full')
                        worker_ui_elements[f'progress_{i}'] = progress

# --- Update Loop ---
def update_ui():
    load_data()
    for i in range(5):
        stats = state.worker_stats.get(str(i), {"requests": 0, "exhausted": False})
        
        health = worker_ui_elements[f'health_{i}']
        icon = worker_ui_elements[f'icon_{i}']
        
        icon.classes(remove='text-red-500 text-green-500 text-slate-700 animate-pulse')
        health.classes(remove='text-red-500 text-green-500 text-slate-500')
        
        if stats.get('exhausted'):
            health.set_text('EXHAUSTED')
            health.classes('text-red-500')
            icon.classes('text-red-500')
        elif stats.get('requests', 0) > 0:
            health.set_text('HEALTHY')
            health.classes('text-green-500')
            icon.classes('text-green-500 animate-pulse')
        else:
            health.set_text('IDLE')
            health.classes('text-slate-500')
            icon.classes('text-slate-700')
            
        progress = worker_ui_elements[f'progress_{i}']
        progress.set_value(min(1.0, stats.get('requests', 0) / 50.0))
        progress.props(f'color={"red" if stats.get("exhausted") else "blue"}')
        
        label = worker_ui_elements[f'label_{i}']
        label.set_text(f'{stats.get("requests", 0)}/50')

ui.timer(1.0, update_ui)
load_data()
ui.run(title="Gemini Hive Dashboard", dark=True, port=8080)
