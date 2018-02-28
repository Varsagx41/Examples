from django.core.management.base import BaseCommand
from time import time
from _shapes import *
from _shapes_manager import *
from _gen_gui import *
import curses


class Command(BaseCommand):

    def handle(self, *args, **options):
        curses.wrapper(self.main)
        # tree = ShapesTree()
        # childs = tree.get_edges(UsersShape, InvitesShape)
        # for child in childs:
        #     print child

    def main(self, screen):
        gui = GUI(screen=screen)
        gui.start()
        gui.quit()