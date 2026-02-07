#!/usr/bin/env python3
"""
Demo Color Prevalence - Shows the new color prevalence analysis
"""

import tkinter as tk
from tkinter import ttk
from color_selection_logic import ColorSelectionLogic, SCREEN_CAPTURE_AVAILABLE

class ColorPrevalenceDemo:
    """Demo of the color prevalence analysis system"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Color Prevalence Analysis Demo")
        self.root.geometry("700x600")
        
        self.color_logic = ColorSelectionLogic()
        self.setup_demo()
        
    def setup_demo(self):
        """Setup the demo interface"""
        
        # Header
        header = ttk.Label(
            self.root,
            text="Color Prevalence Analysis for Ambient Lighting",
            font=("Segoe UI", 12, "bold")
        )
        header.pack(pady=10)
        
        # Status
        status_text = "Screen capture available" if SCREEN_CAPTURE_AVAILABLE else "Screen capture not available (install mss, pillow, numpy)"
        status_color = "green" if SCREEN_CAPTURE_AVAILABLE else "red"
        
        status_label = ttk.Label(
            self.root,
            text=status_text,
            foreground=status_color
        )
        status_label.pack()
        
        # Main layout
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left side - Original preview
        left_frame = ttk.LabelFrame(main_frame, text="Original Screen", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.original_canvas = tk.Canvas(
            left_frame,
            width=280,
            height=210,
            bg="#1a1a1a",
            relief="sunken",
            bd=2
        )
        self.original_canvas.pack()
        
        # Right side - Highlighted preview
        right_frame = ttk.LabelFrame(main_frame, text="Color Prevalence Analysis", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.highlighted_canvas = tk.Canvas(
            right_frame,
            width=280,
            height=210,
            bg="#1a1a1a",
            relief="sunken",
            bd=2
        )
        self.highlighted_canvas.pack()
        
        # Controls
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Color selection
        color_frame = ttk.Frame(controls_frame)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(color_frame, text="Test Color:").pack(side=tk.LEFT)
        
        self.color_var = tk.StringVar(value="#ff0000")
        color_entry = ttk.Entry(color_frame, textvariable=self.color_var, width=10)
        color_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(
            color_frame,
            text="Choose Color",
            command=self.choose_color
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            color_frame,
            text="Analyze",
            command=self.analyze_color
        ).pack(side=tk.LEFT)
        
        # Tolerance control
        tolerance_frame = ttk.Frame(controls_frame)
        tolerance_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tolerance_frame, text="Color Tolerance:").pack(side=tk.LEFT)
        
        self.tolerance_var = tk.DoubleVar(value=0.15)
        tolerance_scale = ttk.Scale(
            tolerance_frame,
            from_=0.05,
            to=0.4,
            variable=self.tolerance_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.on_tolerance_change
        )
        tolerance_scale.pack(side=tk.LEFT, padx=(10, 0))
        
        # Results
        results_frame = ttk.Frame(controls_frame)
        results_frame.pack(fill=tk.X)
        
        self.results_var = tk.StringVar(value="Click 'Analyze' to see color prevalence")
        ttk.Label(results_frame, textvariable=self.results_var, font=("Segoe UI", 10)).pack()
        
        # Dominant colors
        dominant_frame = ttk.LabelFrame(self.root, text="Dominant Screen Colors", padding="10")
        dominant_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.dominant_colors_frame = ttk.Frame(dominant_frame)
        self.dominant_colors_frame.pack(fill=tk.X)
        
        # Initial capture
        self.refresh_preview()
        
    def refresh_preview(self):
        """Refresh the screen preview"""
        if SCREEN_CAPTURE_AVAILABLE:
            self.color_logic.capture_screen_thumbnail()
            self.update_original_preview()
            self.update_dominant_colors()
        
    def update_original_preview(self):
        """Update the original screen preview"""
        self.original_canvas.delete("all")
        
        thumbnail_tk = self.color_logic.get_screen_thumbnail_tk()
        
        if thumbnail_tk:
            self.original_canvas.create_image(
                140, 105,
                image=thumbnail_tk
            )
            # Keep reference
            self.original_canvas.thumbnail_ref = thumbnail_tk
        else:
            self.original_canvas.create_text(
                140, 105,
                text="Screen capture\nunavailable",
                fill="#666666",
                justify=tk.CENTER
            )
    
    def analyze_color(self):
        """Analyze the selected color prevalence"""
        if not SCREEN_CAPTURE_AVAILABLE:
            self.results_var.set("Screen capture not available")
            return
        
        color = self.color_var.get()
        tolerance = self.tolerance_var.get()
        
        # Refresh screen capture
        self.color_logic.capture_screen_thumbnail()
        
        # Analyze prevalence
        prevalence_data = self.color_logic.analyze_color_prevalence(color, tolerance)
        
        if prevalence_data:
            # Update highlighted preview
            self.highlighted_canvas.delete("all")
            
            try:
                from PIL import ImageTk
                highlighted_tk = ImageTk.PhotoImage(prevalence_data['highlighted_image'])
                
                self.highlighted_canvas.create_image(
                    140, 105,
                    image=highlighted_tk
                )
                # Keep reference
                self.highlighted_canvas.highlighted_ref = highlighted_tk
                
            except Exception as e:
                self.highlighted_canvas.create_text(
                    140, 105,
                    text=f"Analysis error:\n{str(e)}",
                    fill="#ff6666",
                    justify=tk.CENTER
                )
            
            # Update results
            prevalence = prevalence_data['prevalence_percent']
            
            if prevalence > 15:
                recommendation = "Excellent for ambient lighting!"
            elif prevalence > 8:
                recommendation = "Good choice for ambient lighting"
            elif prevalence > 3:
                recommendation = "Moderate presence - consider other colors"
            else:
                recommendation = "Low presence - poor choice for ambient lighting"
            
            self.results_var.set(f"{prevalence:.1f}% of screen - {recommendation}")
            
        else:
            self.results_var.set("Analysis failed - check dependencies")
    
    def update_dominant_colors(self):
        """Update dominant colors display"""
        # Clear existing
        for widget in self.dominant_colors_frame.winfo_children():
            widget.destroy()
        
        dominant_colors = self.color_logic.get_dominant_colors(6)
        
        if dominant_colors:
            for i, (color, percentage) in enumerate(dominant_colors):
                color_frame = ttk.Frame(self.dominant_colors_frame)
                color_frame.pack(side=tk.LEFT, padx=5)
                
                # Color button
                color_btn = tk.Button(
                    color_frame,
                    text="",
                    bg=color,
                    width=4,
                    height=2,
                    relief="raised",
                    bd=2,
                    command=lambda c=color: self.select_color(c)
                )
                color_btn.pack()
                
                # Percentage
                ttk.Label(
                    color_frame,
                    text=f"{percentage:.1f}%",
                    font=("Segoe UI", 8)
                ).pack()
        else:
            ttk.Label(
                self.dominant_colors_frame,
                text="No dominant colors found",
                foreground="#666666"
            ).pack()
    
    def select_color(self, color: str):
        """Select a dominant color for analysis"""
        self.color_var.set(color)
        self.analyze_color()
    
    def choose_color(self):
        """Open color chooser"""
        from tkinter import colorchooser
        
        color = colorchooser.askcolor(title="Choose Color to Analyze")
        if color and color[1]:
            self.color_var.set(color[1])
    
    def on_tolerance_change(self, value=None):
        """Handle tolerance change"""
        # Re-analyze if we have a color selected
        if self.color_var.get():
            self.analyze_color()
    
    def run(self):
        """Run the demo"""
        print("Color Prevalence Analysis Demo")
        print("Features:")
        print("- Live screen capture and analysis")
        print("- Color prevalence highlighting")
        print("- Dominant color extraction")
        print("- Adjustable color tolerance")
        print("- Ambient lighting recommendations")
        
        self.root.mainloop()

if __name__ == "__main__":
    demo = ColorPrevalenceDemo()
    demo.run()