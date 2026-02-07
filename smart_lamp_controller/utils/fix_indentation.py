#!/usr/bin/env python3
"""
Recreate the problematic function with correct indentation
"""

# Read the file and fix the problematic function
with open("color_map_window.py", "r") as f:
    lines = f.readlines()

# Find the problematic function and replace it
output_lines = []
for i, line in enumerate(lines):
    if "def update_selection_indicator_from_position(self, position):" in line:
        # Replace the problematic function with correctly indented version
        output_lines.append(
            "    def update_selection_indicator_from_position(self, position):\n"
        )
        output_lines.append(
            '        """Update selection indicator based on saved position"""\n'
        )
        output_lines.append(
            "        width = self.color_map_canvas.winfo_width() or 400\n"
        )
        output_lines.append(
            "        height = self.color_map_canvas.winfo_height() or 300\n"
        )
        output_lines.append("        \n")
        output_lines.append(
            "        # Convert normalized position to canvas coordinates\n"
        )
        output_lines.append("        x = int(position[0] * width)\n")
        output_lines.append("        y = int(position[1] * height)\n")
        output_lines.append("        \n")
        output_lines.append("        self.update_selection_indicator(x, y)\n")
        output_lines.append("\n")
    else:
        output_lines.append(line)

# Write the fixed file
with open("color_map_window.py", "w") as f:
    f.writelines(output_lines)

print("Fixed indentation issue in update_selection_indicator_from_position function")
