import pygame as pg
from math import ceil

class Font:
    def __init__(self, image, padding=1):
        self.image = image
        self.char_key = []
        self.load_font_key('abcdefghijklmnopqrstuvwxyz1234567890.,;-?!_')
        self.char_dict = {}
        self.font_width = self.image.get_width()//len(self.char_key)
        self.font_height = self.image.get_height()
        self.padding = padding
        self.load_font()
    
    def load_font_key(self, chars):
        for char in chars:
            self.char_key.append(char)

    def load_font(self):
        for i in range(len(self.char_key)):
            letter = pg.Surface((self.font_width, self.font_height))
            letter.blit(self.image, (-i*self.font_width, 0))
            if i%2==0:
                letter.set_colorkey((0, 0, 255))
            else:
                letter.set_colorkey((255, 0, 0))
            white = pg.Surface((self.font_width, self.font_height))
            white.fill((255, 255, 255))
            white.blit(letter, (0, 0))
            white.set_colorkey((0, 0, 0))
            self.char_dict[self.char_key[i]] = white
    
    def render(self, screen, text, x, y, colour, size=0, style='left'):
        if size==0:
            size = self.font_width
        
        ratio = size/self.font_width
        scaled_height = ceil(ratio*self.font_height)
        scaled_padding = ceil(ratio*self.padding)
        
        if style=='center':
            x-=(size+scaled_padding)*(len(text)-1)/2
        for char in text:
            if char != ' ':
                char = char.lower()
                letter = self.char_dict[char]
                letter.set_colorkey((255, 255, 255))
                coloured_letter = pg.Surface((self.font_width, self.font_height))
                coloured_letter.fill(colour)
                coloured_letter.blit(letter, (0, 0))
                letter = pg.transform.scale(coloured_letter, (size, scaled_height))
                letter.set_colorkey((0, 0, 0))
                screen.blit(letter, (x-size//2, y-scaled_height//2))
            x+=size+scaled_padding