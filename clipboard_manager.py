# clipboard_manager.py
import pyperclip
import threading
import time
import streamlit as st

class ClipboardManager:
    def __init__(self):
        self.clear_timers = {}
    
    def copy_to_clipboard(self, text, clear_after=30, key="default"):
        """Copy text to clipboard and schedule clearance"""
        try:
            pyperclip.copy(text)
            st.success(f"✅ Copied to clipboard! Will clear in {clear_after} seconds")
            
            # Schedule clearance
            self.schedule_clearance(clear_after, key)
            return True
        except Exception as e:
            st.error(f"❌ Clipboard error: {str(e)}")
            return False
    
    def schedule_clearance(self, clear_after, key):
        """Schedule clipboard clearance"""
        # Cancel any existing timer for this key
        if key in self.clear_timers:
            self.clear_timers[key].cancel()
        
        # Create new timer
        timer = threading.Timer(clear_after, self.clear_clipboard, args=[key])
        timer.daemon = True
        timer.start()
        self.clear_timers[key] = timer
    
    def clear_clipboard(self, key="default"):
        """Clear the clipboard content"""
        try:
            current_content = pyperclip.paste()
            # Only clear if it matches what we expect (optional safety check)
            pyperclip.copy("")  # Clear clipboard
            if key in self.clear_timers:
                del self.clear_timers[key]
        except:
            pass
    
    def cancel_all_timers(self):
        """Cancel all scheduled clearances"""
        for timer in self.clear_timers.values():
            timer.cancel()
        self.clear_timers.clear()

# Global clipboard manager instance
clipboard_manager = ClipboardManager()