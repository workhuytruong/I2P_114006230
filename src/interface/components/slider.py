import pygame as pg
from src.utils import load_img

class Slider:
    def __init__(self, x, y, width, height, initial_value=1.0,
                 track_img_path=None, fill_img_path=None, knob_img_path=None):
        
        self.rect = pg.Rect(x, y, width, height)
        self.knob_rect = pg.Rect(0, 0, 20, height)
        self.value = initial_value
        self.dragging = False

        # Load images
        self.track_img = load_img(track_img_path) if track_img_path else None
        self.fill_img = load_img(fill_img_path) if fill_img_path else None
        self.knob_img = load_img(knob_img_path) if knob_img_path else None

        self.update_knob_position()

    def update_knob_position(self):
        self.knob_rect.x = self.rect.x + int(self.value * (self.rect.width - self.knob_rect.width))
        self.knob_rect.y = self.rect.y

    def update(self, dt: float) -> None:
        self.knob_rect.x = self.rect.x + int(self.value * (self.rect.width - self.knob_rect.width))
        self.knob_rect.y = self.rect.y

    def handle_event(self, event):
        """Handle mouse events for dragging and clicking anywhere."""
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.knob_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                # Start dragging
                self.dragging = True
                # Move knob to clicked position
                x = event.pos[0] - self.rect.x - self.knob_rect.width // 2
                x = max(0, min(x, self.rect.width - self.knob_rect.width))
                self.knob_rect.x = self.rect.x + x
                self.value = x / (self.rect.width - self.knob_rect.width)

        elif event.type == pg.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pg.MOUSEMOTION and self.dragging:
            # Dragging knob smoothly
            x = event.pos[0] - self.knob_rect.width // 2
            x = max(self.rect.x, min(x, self.rect.right - self.knob_rect.width))
            self.knob_rect.x = x
            self.value = (self.knob_rect.x - self.rect.x) / (self.rect.width - self.knob_rect.width)
    def draw(self, screen):
        

        #Track
        if self.track_img:
            track_surf = pg.transform.scale(self.track_img, (self.rect.width, self.rect.height))
            screen.blit(track_surf, self.rect)
        else:
            pg.draw.rect(screen, (100, 100, 100), self.rect, border_radius=5)

        #Fill
        fill_width = int(self.value * self.rect.width)
        fill_rect = pg.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)

        if self.fill_img:
            # Create a scaled image same size as track
            scaled_fill = pg.transform.scale(self.fill_img, (self.rect.width, self.rect.height))
            # Clip only the part we want to show
            clipped = scaled_fill.subsurface((0, 0, fill_width, self.rect.height))
            screen.blit(clipped, fill_rect)
        else:
            pg.draw.rect(screen, (0, 200, 0), fill_rect, border_radius=5)

        #Knob
        if self.knob_img:
            knob_surf = pg.transform.scale(self.knob_img, (self.knob_rect.width, self.knob_rect.height))
            screen.blit(knob_surf, self.knob_rect)
        else:
            pg.draw.rect(screen, (220, 220, 220), self.knob_rect, border_radius=5)
