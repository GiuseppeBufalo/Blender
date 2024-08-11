def wrap_cursor(self, context, event):
    # GRAB_CURSOR bl_option wraps the cursor so in never leaves the region, but we need to 
    # remember this offset so we can reposition the modal HUD to match the cursor jump.

    if self.mouse_x > self.region_border_x -2: # GRAB_CURSOR has a 2 pixel buffer or something. 
        self.cursor_wrap_offset_x += self.region_border_x
    
    elif self.mouse_x < -2:
        self.cursor_wrap_offset_x -= self.region_border_x