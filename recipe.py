"""
Recipe Display Module
Customize how recipes are displayed when the user confirms they want step-by-step instructions.
Edit this file to change the recipe display format, styling, and presentation.
"""

from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, font
import threading


def display_recipe(recipe_text, ingredients=None, recipe_name=None):
    """
    Display a recipe in a formatted, customizable way.
    
    Args:
        recipe_text: The full recipe text/instructions from the AI
        ingredients: Optional list of ingredients (if available)
        recipe_name: Optional name of the recipe
    
    Returns:
        Formatted recipe string ready to display
    """
    # ============================================
    # CUSTOMIZE THE RECIPE DISPLAY BELOW
    # ============================================
    
    # Recipe display template - edit this to change how recipes look
    formatted_recipe = ""
    
    # Header
    if recipe_name:
        formatted_recipe += f"\n{'='*60}\n"
        formatted_recipe += f"  {recipe_name.upper()}\n"
        formatted_recipe += f"{'='*60}\n\n"
    else:
        formatted_recipe += f"\n{'='*60}\n"
        formatted_recipe += f"  RECIPE INSTRUCTIONS\n"
        formatted_recipe += f"{'='*60}\n\n"
    
    # Ingredients section (if provided)
    if ingredients:
        formatted_recipe += "INGREDIENTS:\n"
        formatted_recipe += "-" * 60 + "\n"
        for ingredient in ingredients:
            formatted_recipe += f"  • {ingredient}\n"
        formatted_recipe += "\n"
    
    # Instructions section
    formatted_recipe += "INSTRUCTIONS:\n"
    formatted_recipe += "-" * 60 + "\n"
    
    # Format the recipe text
    # Split by common step indicators and number them
    recipe_lines = recipe_text.split('\n')
    step_number = 1
    
    for line in recipe_lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line already starts with a number or step indicator
        if any(line.lower().startswith(prefix) for prefix in ['step', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']):
            formatted_recipe += f"\n{line}\n"
        else:
            # Add step number if it looks like an instruction
            if len(line) > 20:  # Likely an instruction, not a header
                formatted_recipe += f"  {step_number}. {line}\n"
                step_number += 1
            else:
                formatted_recipe += f"\n{line}\n"
    
    formatted_recipe += f"\n{'='*60}\n"
    formatted_recipe += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    formatted_recipe += f"{'='*60}\n"
    
    return formatted_recipe


def display_recipe_simple(recipe_text):
    """
    Simple recipe display - minimal formatting.
    Edit this function for a simpler recipe display style.
    """
    return f"\n📋 RECIPE:\n{'-'*50}\n{recipe_text}\n{'-'*50}\n"


def display_recipe_fancy(recipe_text, ingredients=None, recipe_name=None):
    """
    Fancy recipe display with enhanced formatting.
    Edit this function for a more elaborate recipe display style.
    """
    formatted = "\n" + "╔" + "═" * 58 + "╗\n"
    
    if recipe_name:
        title = f"  {recipe_name.upper()}"
        formatted += "║" + title.center(58) + "║\n"
    else:
        formatted += "║" + "  RECIPE INSTRUCTIONS".center(58) + "║\n"
    
    formatted += "╠" + "═" * 58 + "╣\n"
    
    if ingredients:
        formatted += "║" + " INGREDIENTS:".ljust(58) + "║\n"
        formatted += "╠" + "─" * 58 + "╣\n"
        for ingredient in ingredients:
            formatted += "║" + f"  • {ingredient}".ljust(58) + "║\n"
        formatted += "╠" + "═" * 58 + "╣\n"
    
    formatted += "║" + " INSTRUCTIONS:".ljust(58) + "║\n"
    formatted += "╠" + "─" * 58 + "╣\n"
    
    # Format instructions
    recipe_lines = recipe_text.split('\n')
    step_number = 1
    for line in recipe_lines:
        line = line.strip()
        if not line:
            continue
        if len(line) > 20:
            formatted += "║" + f"  {step_number}. {line}".ljust(58) + "║\n"
            step_number += 1
        else:
            formatted += "║" + f"  {line}".ljust(58) + "║\n"
    
    formatted += "╚" + "═" * 58 + "╝\n"
    
    return formatted


# ============================================
# CHOOSE WHICH DISPLAY FUNCTION TO USE
# ============================================
# Change this to: display_recipe, display_recipe_simple, or display_recipe_fancy
RECIPE_DISPLAY_FUNCTION = display_recipe


def format_recipe_for_display(recipe_text, ingredients=None, recipe_name=None):
    """
    Main function to format recipe for display.
    Uses the selected display function.
    """
    return RECIPE_DISPLAY_FUNCTION(recipe_text, ingredients, recipe_name)


def show_recipe_window(recipe_text, ingredients=None, recipe_name=None):
    """
    Display recipe in a GUI window.
    Opens a new window with the recipe formatted nicely.
    
    Args:
        recipe_text: The full recipe text/instructions from the AI
        ingredients: Optional list of ingredients (if available)
        recipe_name: Optional name of the recipe
    """
    # Create the main window
    window = tk.Tk()
    
    # ============================================
    # CUSTOMIZE THE WINDOW APPEARANCE BELOW
    # ============================================
    
    # Window configuration - edit these to change appearance
    window.title("JARVIS - Recipe Display")
    window.geometry("800x600")
    window.configure(bg="#1a1a2e")  # Dark blue background (Jarvis style)
    
    # Make window stay on top
    window.attributes("-topmost", True)
    
    # Header frame
    header_frame = tk.Frame(window, bg="#0f3460", height=80)
    header_frame.pack(fill=tk.X, padx=0, pady=0)
    
    # Title
    title_font = font.Font(family="Arial", size=20, weight="bold")
    title_label = tk.Label(
        header_frame,
        text="JARVIS Recipe",
        font=title_font,
        bg="#0f3460",
        fg="#00d4ff",  # Jarvis blue
        pady=20
    )
    title_label.pack()
    
    # Main content frame with scrollbar
    content_frame = tk.Frame(window, bg="#1a1a2e")
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # Text widget with scrollbar
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        wrap=tk.WORD,
        font=font.Font(family="Arial", size=12),
        bg="#16213e",  # Darker blue background
        fg="#ffffff",  # White text
        insertbackground="#00d4ff",  # Jarvis blue cursor
        selectbackground="#00d4ff",
        padx=20,
        pady=20,
        relief=tk.FLAT,
        borderwidth=0
    )
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    # Format and insert recipe content
    formatted_content = ""
    
    # Recipe name
    if recipe_name:
        formatted_content += f"{recipe_name.upper()}\n"
        formatted_content += "=" * 70 + "\n\n"
    else:
        formatted_content += "RECIPE INSTRUCTIONS\n"
        formatted_content += "=" * 70 + "\n\n"
    
    # Ingredients section
    if ingredients:
        formatted_content += "INGREDIENTS:\n"
        formatted_content += "-" * 70 + "\n"
        for ingredient in ingredients:
            formatted_content += f"  • {ingredient}\n"
        formatted_content += "\n"
    
    # Instructions section
    formatted_content += "INSTRUCTIONS:\n"
    formatted_content += "-" * 70 + "\n\n"
    
    # Format instructions
    recipe_lines = recipe_text.split('\n')
    step_number = 1
    
    for line in recipe_lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if line already starts with a number or step indicator
        if any(line.lower().startswith(prefix) for prefix in ['step', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']):
            formatted_content += f"{line}\n\n"
        else:
            # Add step number if it looks like an instruction
            if len(line) > 20:  # Likely an instruction
                formatted_content += f"{step_number}. {line}\n\n"
                step_number += 1
            else:
                formatted_content += f"{line}\n\n"
    
    formatted_content += "\n" + "=" * 70 + "\n"
    formatted_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # Insert formatted content
    text_widget.insert(tk.END, formatted_content)
    text_widget.config(state=tk.DISABLED)  # Make read-only
    
    # Configure text tags for styling (optional - for future customization)
    text_widget.tag_config("title", foreground="#00d4ff", font=font.Font(family="Arial", size=14, weight="bold"))
    text_widget.tag_config("header", foreground="#00d4ff", font=font.Font(family="Arial", size=12, weight="bold"))
    
    # Close button
    close_button = tk.Button(
        window,
        text="Close",
        command=window.destroy,
        bg="#00d4ff",
        fg="#1a1a2e",
        font=font.Font(family="Arial", size=11, weight="bold"),
        relief=tk.FLAT,
        padx=30,
        pady=10,
        cursor="hand2"
    )
    close_button.pack(pady=10)
    
    # Center window on screen
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Run the window (non-blocking)
    window.mainloop()


def show_recipe_window_threaded(recipe_text, ingredients=None, recipe_name=None):
    """
    Show recipe window in a separate thread so it doesn't block the main program.
    """
    thread = threading.Thread(
        target=show_recipe_window,
        args=(recipe_text, ingredients, recipe_name),
        daemon=True
    )
    thread.start()

