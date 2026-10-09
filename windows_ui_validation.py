"""Exercise the packaged application on a Windows runner using isolated data."""
from __future__ import annotations

import ctypes
from contextlib import closing
import json
import math
import os
import sqlite3
import tempfile
import traceback
from datetime import datetime, timedelta
from pathlib import Path

from PIL import ImageGrab


def run_validation(pet_type, output_path: Path) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    report = {"platform": os.name, "checks": [], "screenshots": [], "passed": False}
    app = None
    previous_data = os.environ.get("WATER_PANDA_DATA_DIR")

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report["checks"].append(name)
        (output_path / "progress.json").write_text(json.dumps(report),encoding="utf-8")

    def snapshot(name, window=None):
        target = window or app.root
        app.root.update_idletasks()
        target.update()
        if os.name == "nt":
            ctypes.windll.dwmapi.DwmFlush()
        bbox = (target.winfo_rootx(), target.winfo_rooty(),
                target.winfo_rootx() + target.winfo_width(),
                target.winfo_rooty() + target.winfo_height())
        try:
            image = ImageGrab.grab(bbox=bbox, all_screens=True)
            if len(image.getcolors(maxcolors=16) or []) == 1:
                raise RuntimeError("Capture is uniform; desktop capture unavailable")
            filename = f"{name}.png"
            image.save(output_path / filename)
            report["screenshots"].append(filename)
        except Exception as error:
            report.setdefault("capture_warnings", []).append(str(error))

    def clear_action():
        app.prompt_visible = False
        app.active_alert_kind = ""
        app.active_alert_id = None
        app.state = "normal"
        app.sad_until = None
        app.idle_mood = ""
        app.idle_mood_until = None
        app.current_action = None
        app.pending_edge_action = None
        app.motion_mode = "idle"
        app.cursor_mode.set("Off")
        app.cursor_session_kind = ""
        app.cursor_session_until = None
        app._close_chatter_card()

    try:
        check("Windows runtime", os.name == "nt")
        with tempfile.TemporaryDirectory(prefix="water-panda-ui-", ignore_cleanup_errors=True) as data_dir:
            os.environ["WATER_PANDA_DATA_DIR"] = data_dir
            app = pet_type()
            app.sound_enabled.set(False)
            app.roam_enabled.set(False)
            app.sleep_enabled.set(False)
            app.movement_enabled.set(False)
            app.next_idle_activity = datetime.now() + timedelta(hours=1)
            app.next_reminder = datetime.now() + timedelta(hours=1)
            app.next_hunger = datetime.now() + timedelta(hours=1)
            app.next_chatter = datetime.now() + timedelta(hours=1)
            clear_action()
            app._draw()
            app.root.update()
            check("Panda widget initialized", app.canvas.winfo_width() == 180)
            report["tray_error"] = app.tray.error
            report["tray_icon_registered"] = app.tray.icon_added
            check("Tray message loop initialized", bool(app.tray.hwnd))
            snapshot("idle")

            # Inspect the *immediate* scene, without calling _draw or update:
            # old builds exposed a misplaced cached image until the next tick.
            app._move_root(300,300)
            app.root.update_idletasks()
            app.frame=0
            app._draw()
            def image_anchor():
                item=next(i for i in app.canvas.find_all() if app.canvas.type(i)=="image")
                x,y=app.canvas.coords(item)
                return (app.root.winfo_x()+x,app.root.winfo_y()+y)
            anchor=image_anchor()
            for i in range(20):
                app._show_chatter("Transition check",seconds=10)
                check(f"Immediate cloud opening keeps rendered anchor {i}",image_anchor()==anchor)
                app._close_chatter_card()
                check(f"Immediate cloud closing keeps rendered anchor {i}",image_anchor()==anchor)
            from tkinter import BooleanVar
            from threading import Timer
            menu_finished=BooleanVar(master=app.root,value=False)
            menu_observed=[]
            menu_position=[]
            gui_thread=ctypes.windll.kernel32.GetCurrentThreadId()
            detector=pet_type._context_menu_active.__globals__["windows_menu_active"]
            def inspect_and_dismiss_native_menu():
                try:
                    menu_observed.append(detector(gui_thread))
                    menu_position.append((app.pet_x,app.pet_y))
                finally:
                    ctypes.windll.user32.keybd_event(0x1B,0,0,0)
                    ctypes.windll.user32.keybd_event(0x1B,0,2,0)
            position=(app.pet_x,app.pet_y)
            timer=Timer(0.4,inspect_and_dismiss_native_menu)
            timer.daemon=True
            timer.start()
            app.menu.post(500,350)
            app.root.after(700,menu_finished.set,True)
            app.root.wait_variable(menu_finished)
            app.menu.unpost()
            app.menu.grab_release()
            check("Native Windows menu state detected",menu_observed==[True])
            check("Posted native menu holds panda position",menu_position==[position])
            check("Menu dismissal resumes behavior",not app._context_menu_active())

            app.show_prompt()
            app.attention_started_at = datetime.now() - timedelta(seconds=5)
            app._draw()
            snapshot("water_cloud")
            check("Water cloud is drawn on the panda canvas", len(app.canvas.find_all()) > 10)
            original_scaling = float(app.root.tk.call("tk", "scaling"))
            for percent in (100,125,150):
                app.root.tk.call("tk", "scaling", percent/100*96/72)
                app._draw()
                app.root.update_idletasks()
                for tag in ("amount_100","amount_200","amount_300","not_yet","water_snooze"):
                    shape,text = app.canvas.find_withtag(tag)
                    shape_box = app.canvas.bbox(shape)
                    text_box = app.canvas.bbox(text)
                    check(f"Water label fits at {percent}%: {tag}", text_box[0]>=shape_box[0] and text_box[2]<=shape_box[2])
                snapshot(f"water_text_scale_{percent}")
            app.root.tk.call("tk", "scaling", original_scaling)
            app.record_water(200)
            app.record_water(200)
            with closing(sqlite3.connect(app.database_path)) as db, db:
                row = db.execute("SELECT COUNT(*), SUM(millilitres) FROM water_entries").fetchone()
            check("Water response logs once", row == (1, 200))
            check("Water response bows", app.idle_mood == "bow")

            clear_action()
            app.show_prompt()
            app.answer_not_yet()
            due = app.next_reminder
            check("Not yet starts a bounded sad reaction", app.state == "sad" and app.sad_until is not None)
            app._update_water_response(datetime.now() + timedelta(seconds=9))
            check("Not yet recovers without pausing water", app.state == "normal" and app.next_reminder == due)
            clear_action()
            app.show_prompt()
            app.snooze_water()
            check("Water snooze sets ten minutes", 590 < (app.next_reminder - datetime.now()).total_seconds() <= 600)
            app.pause_reminders()
            check("Water pause sets one hour", app.reminders_paused_until is not None)
            app.resume_reminders()
            check("Water resume clears pause", app.reminders_paused_until is None)

            clear_action()
            app.water_window_enabled.set(True)
            app.water_start.set("9 AM")
            app.water_end.set("9 PM")
            app._water_schedule_settings_changed()
            check("Water hours normalize and save", app.water_start.get()=="09:00" and app.water_end.get()=="21:00")
            late = datetime(2026,10,5,22)
            app.show_prompt()
            app.water_prompt_manual = False
            app._enforce_water_window(late)
            check("Water hours close automatic offers", not app.prompt_visible and app.state=="normal")
            check("Water hours schedule next opening", app.next_reminder >= datetime(2026,10,6,9))
            app.show_prompt()
            check("Water now remains available outside hours", app.prompt_visible and app.water_prompt_manual)
            app.water_window_enabled.set(False)
            app.answer_not_yet()
            clear_action()
            app._play_activity("log")
            check("Log starts cheerful play without bored travel", app.idle_mood=="log_play" and not app.pending_edge_action)
            app.idle_mood_started_at=datetime.now()-timedelta(seconds=6)
            app._draw()
            snapshot("log_play")

            clear_action()
            app._show_general_alert("Stand and stretch", "Move with your panda", "movement")
            app._draw()
            snapshot("movement_cloud")
            app._snooze_active_alert()
            check("Movement snooze sets ten minutes", 590 < (app.next_movement_reminder - datetime.now()).total_seconds() <= 600)

            clear_action()
            now = datetime.now().astimezone()
            with closing(sqlite3.connect(app.database_path)) as db, db:
                reminder_id = db.execute("INSERT INTO personal_reminders(title,due_at,status,created_at) VALUES (?,?,?,?)",
                                         ("Meeting at 1 PM", (now-timedelta(minutes=1)).isoformat(timespec="seconds"),
                                          "scheduled", now.isoformat(timespec="seconds"))).lastrowid
            app.show_prompt()
            app._check_scheduled_reminders(datetime.now())
            check("Personal reminder preempts water without overlap", app.active_alert_kind == "personal" and not app.prompt_visible)
            check("Due personal reminder displays", app.active_alert_kind == "personal" and app.active_alert_id == reminder_id)
            app._draw()
            snapshot("watch_cloud")
            app._snooze_active_alert()
            with closing(sqlite3.connect(app.database_path)) as db, db:
                due_at, status = db.execute("SELECT due_at,status FROM personal_reminders WHERE reminder_id=?", (reminder_id,)).fetchone()
            check("Personal snooze stays scheduled", status == "scheduled" and datetime.fromisoformat(due_at) > now + timedelta(minutes=9))
            check("Deferred water offer resumes", app.prompt_visible)
            app.answer_not_yet()
            app._show_general_alert("Meeting at 1 PM", "Your reminder", "personal", reminder_id)
            app._complete_active_alert()
            with closing(sqlite3.connect(app.database_path)) as db, db:
                status = db.execute("SELECT status FROM personal_reminders WHERE reminder_id=?", (reminder_id,)).fetchone()[0]
            check("Personal reminder completes", status == "done")

            clear_action()
            app.show_history()
            app.root.update()
            check("Panda Home opens", app.history_window.winfo_exists())
            snapshot("panda_home", app.history_window)
            check("Panda does not cover Panda Home", not app.root.winfo_viewable())
            for index, name in enumerate(("home", "history", "reminders", "settings", "activities", "behaviour", "themes")):
                app.studio_notebook.select(index)
                app.root.update_idletasks()
                snapshot(f"page_{name}", app.history_window)
                check(f"Panda Home navigation: {name}", True)
            app.behavior_canvas.yview_moveto(1)
            app.root.update_idletasks()
            snapshot("behaviour_bottom", app.history_window)
            check("Behaviour scroll reaches the bottom", app.behavior_canvas.yview()[1] > 0.99)
            entry_module = __import__(pet_type.__module__)
            picker = entry_module.filedialog.asksaveasfilename
            csv_path = Path(data_dir)/"export.csv"
            entry_module.filedialog.asksaveasfilename = lambda **kwargs: str(csv_path)
            try:
                app.export_history()
            finally:
                entry_module.filedialog.asksaveasfilename = picker
            check("CSV export contains recorded intake", csv_path.exists() and "200" in csv_path.read_text(encoding="utf-8-sig"))
            app.undo_latest_entry()
            with closing(sqlite3.connect(app.database_path)) as db:
                count = db.execute("SELECT COUNT(*) FROM water_entries").fetchone()[0]
            check("Undo requires inline confirmation", count == 1 and app.undo_confirmation_id is not None)
            app.undo_latest_entry()
            with closing(sqlite3.connect(app.database_path)) as db:
                count = db.execute("SELECT COUNT(*) FROM water_entries").fetchone()[0]
            check("Confirmed undo removes exactly the latest entry", count == 0)
            app._hide_studio()
            app.reminder_title_var.set("")
            app.add_personal_reminder()
            check("Reminder validation is inline", bool(app.reminder_feedback_var.get()))

            from_module = __import__(pet_type.__module__)
            # Frozen entry-point classes belong to __main__; the catalog remains there.
            catalog = getattr(from_module, "ACTIVITY_LABELS")
            for key in catalog:
                clear_action()
                app._play_activity(key)
                app._draw()
                app.root.update_idletasks()
                check(f"Activity dispatch and render: {key}", True)

            clear_action()
            left, top, right, bottom = app._screen_bounds()
            app.pet_x = float(left+20)
            app.pet_y = float(top+100)
            app._move_root(round(app.pet_x), round(app.pet_y))
            app.cursor_mode.set("Follow")
            # Keep runner inactivity from scheduling a yawn while testing pointer motion.
            app.user_was_inactive = False
            app.inactivity_yawn_shown = False
            app.system_idle_seconds_cache = 0
            app.last_system_idle_check = datetime.now()
            point = (min(right-20, left+900), min(bottom-20, top+650))
            ctypes.windll.user32.SetCursorPos(*point)
            app.root.update()
            app._close_chatter_card()
            app.idle_mood = ""
            app.motion_mode = "idle"
            check("Windows pointer was positioned", app.root.winfo_pointerxy() == point)
            before = math.hypot(point[0]-app.pet_x-90, point[1]-app.pet_y-92)
            app._check_cursor_reaction(datetime.now())
            after = math.hypot(point[0]-app.pet_x-90, point[1]-app.pet_y-92)
            check("Live Windows pointer follow moves closer", after < before)
            app._draw()
            snapshot("walk")
            app._mouse_enter(None)
            check("Hover does not interrupt live follow", not app.chatter_until)
            app._show_chatter("A deliberate pause", seconds=3)
            check("Deliberate chatter pauses locomotion", app._locomotion_paused())
            position = (app.pet_x, app.pet_y)
            app._check_cursor_reaction(datetime.now())
            check("Hover cloud holds pointer-follow position", position == (app.pet_x, app.pet_y))
            app._draw()
            check("Paused locomotion resets walk phase", app.gait_signature is None)
            snapshot("hover_standing")
            app.chatter_until = None
            app.chatter_text = ""
            app._close_chatter_card()
            app._check_cursor_reaction(datetime.now())
            check("Follow resumes after hover cloud closes", position != (app.pet_x, app.pet_y))
            app._draw()
            for name, point, target in (
                ("top_left",(left,top),(left,top+100)),
                ("bottom_right",(right-1,bottom-1),(right-180,top+100)),
            ):
                ctypes.windll.user32.SetCursorPos(*point)
                for _ in range(2000):
                    app._check_cursor_reaction(datetime.now())
                    if app.cursor_at_rest:
                        break
                app.root.update_idletasks()
                check(f"Follow reaches physical screen edge: {name}",
                      abs(app.pet_x-target[0])<1 and abs(app.pet_y-target[1])<1)
                check(f"Pet canvas stays visible at edge: {name}",
                      left<=app.pet_x<=right-180 and top<=app.pet_y<=bottom-184)
                app._draw()
                snapshot(f"edge_{name}")

            clear_action()
            for name, position in (
                ("top_left", (left, top)), ("top_right", (right-180, top)),
                ("bottom_left", (left, bottom-184)), ("bottom_right", (right-180, bottom-184)),
            ):
                app._move_root(*position)
                app.root.update_idletasks()
                app.show_prompt()
                app._draw()
                check(f"Water cloud preserves pet at {name}", (app.pet_x, app.pet_y) == position)
                cloud_bounds = app.canvas.bbox("cloud")
                check(f"Water cloud visible at {name}", cloud_bounds and cloud_bounds[0]>=0 and cloud_bounds[1]>=0 and cloud_bounds[2]<=app.width and cloud_bounds[3]<=app.height)
                positions = [app.canvas.bbox(app.canvas.find_withtag(tag)[1])[0] for tag in ("amount_100", "amount_200", "amount_300")]
                check(f"Water amounts retain reading order at {name}", positions == sorted(positions))
                snapshot(f"water_edge_{name}")
                app.snooze_water()
                app._close_chatter_card()
                app.root.update_idletasks()
                check(f"Closing cloud preserves pet at {name}", (app.pet_x, app.pet_y) == position)


            clear_action()
            app.hungry = True
            app.hunger_requested = True
            app.feed_panda()
            check("Bamboo feeding clears hunger", not app.hungry and app.idle_mood == "feed")
            app._draw()
            snapshot("feed")
            clear_action()
            app.theme_mode.set("diwali")
            app._draw()
            check("Theme prop is rendered on panda canvas", len(app.canvas.find_withtag("season_prop")) == 1)
            snapshot("theme_diwali_idle")
            app.show_prompt()
            app._draw()
            check("Festival prop stays out of water offer", not app.canvas.find_withtag("season_prop"))
            check("Festival tint reaches water cloud", any(app.canvas.itemcget(i,"fill") == "#FFF2D9" for i in app.canvas.find_withtag("cloud") if app.canvas.type(i)=="polygon"))
            snapshot("theme_diwali_water")
            app.answer_not_yet()
            clear_action()
            for key in from_module.PROP_KEYS:
                app.theme_mode.set(key)
                app._draw()
                check(f"Festival prop loaded: {key}", bool(app.canvas.find_withtag("season_prop")))
            app.theme_mode.set("shiva")
            app.next_theme_activity=datetime.now()-timedelta(seconds=1)
            app._check_theme_activity(datetime.now())
            check("Shivaratri uses quiet meditation", app.idle_mood=="meditate")
            app.theme_mode.set("Auto")
            app.birthday.set("10-09")
            app._save_settings()
            stored=json.loads(app.settings_path.read_text())
            check("Festival and birthday settings persist", stored["theme_mode"]=="Auto" and stored["birthday"]=="10-09")
            check("Settings persist in isolated data", app.settings_path.exists())
            report["passed"] = True
            app.close()
            app = None
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if app is not None:
            try:
                app.close()
            except Exception:
                pass
        if previous_data is None:
            os.environ.pop("WATER_PANDA_DATA_DIR", None)
        else:
            os.environ["WATER_PANDA_DATA_DIR"] = previous_data
        (output_path / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit(1)
