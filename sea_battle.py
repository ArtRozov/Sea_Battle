import pygame
import sys
import random
import copy

BLUE = (0, 238, 238)
LIGHT_BLUE = (0, 205, 205)
BLACK = (0, 0, 0)
GREEN_BLUE = (0, 153, 153)
RED = (255, 0, 0)

block_size = 50
left_margin = 5 * block_size
upper_margin = 2 * block_size
size = (left_margin + 30 * block_size, upper_margin + 15 * block_size)
LETTERS = "ABCDEFGHIJ"

pygame.init()

screen = pygame.display.set_mode(size)
pygame.display.set_caption("SEABATTLE")
font_size = int(block_size / 1.5)
font = pygame.font.SysFont('notosans', font_size)
game_over_font_size = 3 * block_size
game_over_font = pygame.font.SysFont('notosans', game_over_font_size)
battle_sea_font_size = 4 * block_size
battle_sea_font = pygame.font.SysFont('notosans', battle_sea_font_size)
first_font_size = 2 * block_size
first_font = pygame.font.SysFont('notosans', first_font_size)

computer_available_to_fire_set = {(x, y)
                                  for x in range(16, 26) for y in range(1, 11)}
around_last_computer_hit_set = set()
dotted_set_for_computer_not_to_shoot = set()
hit_blocks_for_computer_not_to_shoot = set()
last_hits_list = []
hit_blocks = set()
dotted_set = set()
user_steps = set()
computer_steps = set()
destroyed_computer_ships = []


class Player:
    def __init__(self, name):
        self.name = name


class Field:
    def __init__(self, offset, player):
        self.offset = offset
        self.name = player.name
        self.__draw_field()
        self.__add_nums_to_field()
        self.__sign_field()

    def __draw_field(self):
        """Отрисовка поля"""
        for i in range(11):
            # Горизонтальные
            pygame.draw.line(screen, BLACK, (left_margin + self.offset * block_size, upper_margin + i * block_size),
                             (left_margin + (10 + self.offset) * block_size, upper_margin + i * block_size), 1)
            # Вертикальные
            pygame.draw.line(screen, BLACK, (left_margin + (i + self.offset) * block_size, upper_margin),
                             (left_margin + (i + self.offset) * block_size, upper_margin + 10 * block_size), 1)

    def __add_nums_to_field(self):
        """Отрисовка букв и цифр над полями"""
        for i in range(10):
            num_ver = font.render(str(i + 1), True, BLACK)
            letters_hor = font.render(LETTERS[i], True, BLACK)
            num_ver_width = num_ver.get_width()
            num_ver_height = num_ver.get_height()
            letters_hor_width = letters_hor.get_width()
            # Номера
            screen.blit(num_ver, (left_margin - (block_size // 2 + num_ver_width // 2) + self.offset * block_size,
                                  upper_margin + i * block_size + (block_size // 2 - num_ver_height // 2)))
            # Буквы
            screen.blit(letters_hor, (left_margin + i * block_size + (block_size // 2 -
                                                                      letters_hor_width // 2) + self.offset * block_size,
                                      upper_margin + 10 * block_size))

    def __sign_field(self):
        """Подписывает, чьё поле"""
        player = font.render(self.name, True, BLACK)
        sign_width = player.get_width()
        screen.blit(player, (left_margin + 5 * block_size - sign_width // 2 +
                             self.offset * block_size, upper_margin - block_size // 2 - font_size))


class Button:

    def __init__(self, x_offset, button_title, my_font, num_of_y, message_to_show):
        self.__title = button_title
        self.__title_width, self.__title_height = my_font.size(self.__title)
        self.__message = message_to_show
        self.__button_width = self.__title_width + block_size
        self.__button_height = self.__title_height + block_size
        self.__x_start = x_offset
        self.__y_start = upper_margin + num_of_y * block_size + self.__button_height
        self.rect_for_draw = self.__x_start, self.__y_start, self.__button_width, self.__button_height
        self.rect = pygame.Rect(self.rect_for_draw)
        self.__rect_for_button_title = self.__x_start + self.__button_width / 2 - self.__title_width / 2, \
                                       self.__y_start + self.__button_height / 2 - self.__title_height / 2
        self.__color = BLACK
        self.__my_font = my_font

    def draw_button(self, color=None):
        """Отрисовка кнопки"""
        if not color:
            color = self.__color
        pygame.draw.rect(screen, color, self.rect_for_draw)
        text_to_blit = self.__my_font.render(self.__title, True, BLUE)
        screen.blit(text_to_blit, self.__rect_for_button_title)

    def change_color_on_hover(self):
        """При наведении мышки меняет цвет"""
        mouse = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse):
            self.draw_button(GREEN_BLUE)

    def print_message_for_button(self):
        """Пояснительное сообщение"""
        message_width, message_height = font.size(self.__message)
        rect_for_message = self.__x_start / 2 - message_width / \
                           2, self.__y_start + self.__button_height / 2 - message_height / 2
        text = font.render(self.__message, True, BLACK)
        screen.blit(text, rect_for_message)


class Ships:
    def __init__(self, offset):
        self.offset = offset
        self.available_blocks = {(x, y) for x in range(
            1 + self.offset, 11 + self.offset) for y in range(1, 11)}
        self.ships_set = set()
        self.ships = self.__populate_field()
        self.orientation = None
        self.direction = None

    def __create_start_block(self, available_blocks):
        # 0 - горизонтально, 1 - вертикально
        self.orientation = random.randint(0, 1)
        # Для обычного случая(вправо/вверх):1. -1 - в других случаях
        self.direction = random.choice((-1, 1))
        x, y = random.choice(tuple(available_blocks))
        return x, y, self.orientation, self.direction

    def __create_ship(self, number_of_blocks, available_blocks):
        """Создание корабля"""
        ship_coordinates = []
        x, y, self.orientation, self.direction = self.__create_start_block(available_blocks)
        for _ in range(number_of_blocks):
            ship_coordinates.append((x, y))
            if self.orientation:
                self.direction, y = self.__get_new_block_for_ship(y, self.direction, self.orientation, ship_coordinates)
            else:
                self.direction, x = self.__get_new_block_for_ship(x, self.direction, self.orientation, ship_coordinates)
        if self.__is_ship_valid(ship_coordinates):
            return ship_coordinates
        return self.__create_ship(number_of_blocks, available_blocks)

    def __get_new_block_for_ship(self, coordinate, direction, orientation, ship_coordinates):
        self.direction = direction
        self.orientation = orientation
        if (coordinate <= 1 - self.offset * (self.orientation - 1) and self.direction == -1) or (
                coordinate >= 10 - self.offset * (self.orientation - 1) and self.direction == 1):
            self.direction *= -1
            return self.direction, ship_coordinates[0][self.orientation] + self.direction
        else:
            return self.direction, ship_coordinates[-1][self.orientation] + self.direction

    def __is_ship_valid(self, new_ship):
        """Проверка на валидность корабля(все клетки свободны на которые мы хотим поставить корабль)"""
        ship = set(new_ship)
        return ship.issubset(self.available_blocks)

    def __add_new_ship_to_set(self, new_ship):
        """Создаём корабль"""
        self.ships_set.update(new_ship)

    def __update_available_blocks_for_creating_ships(self, new_ship):
        """Обновляем валидные клетки"""
        for elem in new_ship:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if self.offset <= (elem[0] + i) <= 11 + self.offset and 0 <= (elem[1] + i) <= 11:
                        self.available_blocks.discard((elem[0] + i, elem[1] + j))

    def __populate_field(self):
        """Создаёт все нужные виды кораблей(Авто метод)"""
        ships_coordinates_list = []
        for number_of_blocks in range(4, 0, -1):
            for _ in range(5 - number_of_blocks):
                new_ship = self.__create_ship(
                    number_of_blocks, self.available_blocks)
                ships_coordinates_list.append(new_ship)
                self.__add_new_ship_to_set(new_ship)
                self.__update_available_blocks_for_creating_ships(new_ship)
        return ships_coordinates_list


def computer_shoots(set_to_shoot_from):
    """Выбор, куда стрелять"""
    pygame.time.delay(500)
    computer_fired_block = random.choice(tuple(set_to_shoot_from))
    computer_available_to_fire_set.discard(computer_fired_block)
    return computer_fired_block


def hit_or_miss(fired_block, opponents_ships_list, computer_turn, opponents_ships_list_original_copy,
                opponents_ships_set):
    global computer_steps
    global user_steps
    global last_hits_list
    global destroyed_computer_ships
    flag = True
    if computer_turn:
        computer_steps.add(fired_block)
    else:
        if fired_block in user_steps:
            flag = False
        user_steps.add(fired_block)
    if flag:
        for elem in opponents_ships_list:
            diagonal_only = True
            if fired_block in elem:
                ind = opponents_ships_list.index(elem)
                if len(elem) == 1:
                    diagonal_only = False
                update_dotted_and_hit_set(fired_block, computer_turn, diagonal_only)
                elem.remove(fired_block)
                opponents_ships_set.discard(fired_block)
                if computer_turn:
                    last_hits_list.append(fired_block)
                    update_around_last_computer_hit(fired_block, True)
                if not elem:
                    update_destroyed_ships(
                        ind, computer_turn, opponents_ships_list_original_copy)
                    if computer_turn:
                        last_hits_list.clear()
                        around_last_computer_hit_set.clear()
                    else:
                        destroyed_computer_ships.append(computer.ships[ind])
                return True
        add_missed_block_to_dotted_set(fired_block)
        if computer_turn:
            update_around_last_computer_hit(fired_block, False)
        return False
    else:
        return True


def update_destroyed_ships(ind, computer_turn, opponents_ships_list_copy):
    ship = sorted(opponents_ships_list_copy[ind])
    for i in range(-1, 1):
        update_dotted_and_hit_set(ship[i], computer_turn, False)


def update_around_last_computer_hit(fired_block, computer_hits):
    global around_last_computer_hit_set, computer_available_to_fire_set
    global dotted_set_for_computer_not_to_shoot
    global hit_blocks_for_computer_not_to_shoot
    if computer_hits and fired_block in around_last_computer_hit_set:
        around_last_computer_hit_set = computer_second_hit()
    elif computer_hits and fired_block not in around_last_computer_hit_set:
        computer_first_hit(fired_block)
    elif not computer_hits:
        around_last_computer_hit_set.discard(fired_block)

    around_last_computer_hit_set -= dotted_set_for_computer_not_to_shoot
    around_last_computer_hit_set -= hit_blocks_for_computer_not_to_shoot
    computer_available_to_fire_set -= around_last_computer_hit_set
    computer_available_to_fire_set -= dotted_set_for_computer_not_to_shoot


def computer_first_hit(fired_block):
    """При первом попадании формируем временный список из 4ёх направлений, куда можем выстрелить"""
    x_hit, y_hit = fired_block
    if x_hit > 16:
        around_last_computer_hit_set.add((x_hit - 1, y_hit))
    if x_hit < 25:
        around_last_computer_hit_set.add((x_hit + 1, y_hit))
    if y_hit > 1:
        around_last_computer_hit_set.add((x_hit, y_hit - 1))
    if y_hit < 10:
        around_last_computer_hit_set.add((x_hit, y_hit + 1))


def computer_second_hit():
    """Вызывается в тех случаях, когда знаем направление корабля"""
    last_hits_list.sort()
    around_hit_set = set()
    for i in range(len(last_hits_list) - 1):
        x1 = last_hits_list[i][0]
        x2 = last_hits_list[i + 1][0]
        y1 = last_hits_list[i][1]
        y2 = last_hits_list[i + 1][1]
        if x1 == x2:
            if y1 > 1:
                around_hit_set.add((x1, y1 - 1))
            if y2 < 10:
                around_hit_set.add((x1, y2 + 1))
        elif y1 == y2:
            if x1 > 16:
                around_hit_set.add((x1 - 1, y1))
            if x2 < 25:
                around_hit_set.add((x2 + 1, y1))
    return around_hit_set


def update_dotted_and_hit_set(fired_block, computer_turn, diagonal_only=True):
    global dotted_set
    global hit_blocks
    x, y = fired_block
    a = 15 * computer_turn
    b = 11 + 15 * computer_turn
    hit_blocks_for_computer_not_to_shoot.add(fired_block)
    hit_blocks.add(fired_block)
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (not diagonal_only or i != 0 and j != 0) and a < x + i < b and 0 < y + j < 11:
                if not computer_turn:
                    user_steps.add((x + i, y + j))
                add_missed_block_to_dotted_set((x + i, y + j))
    dotted_set -= hit_blocks


def add_missed_block_to_dotted_set(fired_block):
    """Добавляет промахи"""
    dotted_set.add(fired_block)
    dotted_set_for_computer_not_to_shoot.add(fired_block)


# Функции отрисовки


def draw_ships(ships_coordinates_list):
    """Отрисовка кораблей"""
    for elem in ships_coordinates_list:
        ship = sorted(elem)
        x_start = ship[0][0]
        y_start = ship[0][1]
        ship_width = block_size * len(ship)
        ship_height = block_size
        if len(ship) > 1 and ship[0][0] == ship[1][0]:
            ship_width, ship_height = ship_height, ship_width
        x = block_size * (x_start - 1) + left_margin
        y = block_size * (y_start - 1) + upper_margin
        pygame.draw.rect(
            screen, BLACK, ((x, y), (ship_width, ship_height)), width=block_size // 10)


def draw_from_dotted_set(dotted_set_to_draw_from):
    """Рисует '.', отмечающее промах"""
    for elem in dotted_set_to_draw_from:
        pygame.draw.circle(screen, BLACK, (block_size * (
                elem[0] - 0.5) + left_margin, block_size * (elem[1] - 0.5) + upper_margin), block_size // 6)


def draw_hit_blocks(hit_blocks_to_draw_from):
    """Рисует 'X', отмечающее попадание"""
    for block in hit_blocks_to_draw_from:
        x1 = block_size * (block[0] - 1) + left_margin
        y1 = block_size * (block[1] - 1) + upper_margin
        pygame.draw.line(screen, BLACK, (x1, y1),
                         (x1 + block_size, y1 + block_size), block_size // 6)
        pygame.draw.line(screen, BLACK, (x1, y1 + block_size),
                         (x1 + block_size, y1), block_size // 6)


def show_message_at_rect_center(message, rect, which_font=font, color=RED):
    """Отрисовка сообщений"""
    message_width, message_height = which_font.size(message)
    message_rect = pygame.Rect(rect)
    x_start = message_rect.centerx - message_width / 2
    y_start = message_rect.centery - message_height / 2
    background_rect = pygame.Rect(
        x_start - block_size / 2, y_start, message_width + block_size, message_height)
    message_to_blit = which_font.render(message, True, color)
    screen.fill(BLUE, background_rect)
    screen.blit(message_to_blit, (x_start, y_start))


def ship_is_valid(ship_set, blocks_for_manual_drawing):
    """Проверка на совместимость кораблей(если корабли касаются друг друга, то False)"""
    return ship_set.isdisjoint(blocks_for_manual_drawing)


def check_ships_numbers(ship, num_ships_list):
    """Проверка на количество кораблей
    если пользователь ввёл больше кораблей одного типа, чем нужно, то мы отвергаем этот корабль"""
    return (5 - len(ship)) > num_ships_list[len(ship) - 1]


def update_used_blocks(ship, method):
    for block in ship:
        for i in range(-1, 2):
            for j in range(-1, 2):
                method((block[0] + i, block[1] + j))


# Создаём корабли компьютера
computer = Ships(0)
computer_ships_working = copy.deepcopy(computer.ships)

# Создаём кнопки с соответствующими сообщениями
auto_button_place = left_margin + 17 * block_size
manual_button_place = left_margin + 20 * block_size
centre_button_place = left_margin + 7.5 * block_size
how_to_create_ships_message = "Вы хотите автоматически расставить корабли?"
auto_button = Button(auto_button_place, "ДА", font, 10, how_to_create_ships_message)
manual_button = Button(manual_button_place, "НЕТ", font, 10,
                       how_to_create_ships_message)

del_message = "Чтобы удалить последний корабль, нажмите кнопку"
del_button_place = left_margin + 12 * block_size
del_button = Button(del_button_place, "Удалить", font, 10, del_message)

thanks_message = "Спасибо за игру!"
quit_button = Button(manual_button_place - 7*block_size, "Выйти из игры", font, 10, thanks_message)

first_quit_button = Button(centre_button_place + 2 * block_size, "Выход", first_font, 8, "")

first_begin_button = Button(centre_button_place, "Начало игры", first_font, 5, "")

again_button = Button(manual_button_place - 13 * block_size, "На главный экран", font, 10, thanks_message)


def main():
    global computer_available_to_fire_set
    global around_last_computer_hit_set
    global dotted_set_for_computer_not_to_shoot
    global hit_blocks_for_computer_not_to_shoot
    global last_hits_list
    global hit_blocks
    global dotted_set
    global user_steps
    global computer_steps
    global destroyed_computer_ships
    global computer
    global computer_ships_working
    ready_to_play = False
    ships_creation_not_decided = True
    ships_not_created = True
    drawing = False
    game_over = False
    computer_turn = False
    start = (0, 0)
    ship_size = (0, 0)

    rect_for_fields = (0, 0, size[0], upper_margin + 12 * block_size)
    rect_for_messages_and_buttons = (0, upper_margin + 11 * block_size, size[0], 5 * block_size)
    message_rect_for_drawing_ships = (del_button.rect_for_draw[0] + del_button.rect_for_draw[2],
                                      upper_margin + 11 * block_size,
                                      size[0] - (del_button.rect_for_draw[0] + del_button.rect_for_draw[2]),
                                      4 * block_size)
    message_rect_computer = (left_margin - 2 * block_size, upper_margin +
                             11 * block_size, 14 * block_size, 4 * block_size)
    message_rect_user = (left_margin + 15 * block_size, upper_margin +
                         11 * block_size, 10 * block_size, 4 * block_size)

    user_ships_to_draw = []
    user_ships_set = set()
    used_blocks_for_manual_drawing = set()
    num_ships_list = [0, 0, 0, 0]
    while not ready_to_play:
        screen.fill(BLUE)
        show_message_at_rect_center("Добро пожаловать", (0, 0, size[0], size[1] - 12 * block_size), game_over_font,
                                    BLACK)
        show_message_at_rect_center("в", (0, 0, size[0], size[1] - 8 * block_size), game_over_font, BLACK)
        show_message_at_rect_center("МОРСКОЙ БОЙ", (0, 0, size[0], size[1] - 3 * block_size), battle_sea_font)
        first_begin_button.draw_button()
        first_begin_button.change_color_on_hover()
        first_quit_button.draw_button()
        first_quit_button.change_color_on_hover()
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and first_quit_button.rect.collidepoint(mouse):
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and first_begin_button.rect.collidepoint(mouse):
                ready_to_play = True
        pygame.display.update()
    screen.fill(BLUE)
    comp = Player("КОМПЬЮТЕР")
    user = Player("ВЫ")
    computer_field = Field(0, comp)
    user_field = Field(15, user)
    while ships_creation_not_decided:
        auto_button.draw_button()
        manual_button.draw_button()
        auto_button.change_color_on_hover()
        manual_button.change_color_on_hover()
        auto_button.print_message_for_button()

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
                ships_creation_not_decided = False
                ships_not_created = False
            # При нажатии кнопки "Да" создаём автоматически корабли
            elif event.type == pygame.MOUSEBUTTONDOWN and auto_button.rect.collidepoint(mouse):
                user = Ships(15)
                user_ships_to_draw = user.ships
                user_ships_working = copy.deepcopy(user.ships)
                user_ships_set = user.ships_set
                ships_creation_not_decided = False
                ships_not_created = False
            elif event.type == pygame.MOUSEBUTTONDOWN and manual_button.rect.collidepoint(mouse):
                ships_creation_not_decided = False

        pygame.display.update()
        screen.fill(BLUE, rect_for_messages_and_buttons)

    while ships_not_created:
        screen.fill(BLUE, rect_for_fields)
        computer_field = Field(0, comp)
        user_field = Field(15, user)
        del_button.draw_button()
        del_button.print_message_for_button()
        del_button.change_color_on_hover()
        mouse = pygame.mouse.get_pos()
        if not user_ships_to_draw:
            del_button.draw_button(LIGHT_BLUE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ships_not_created = False
                game_over = True
            elif del_button.rect.collidepoint(mouse) and event.type == pygame.MOUSEBUTTONDOWN:
                if user_ships_to_draw:
                    screen.fill(BLUE, message_rect_for_drawing_ships)
                    deleted_ship = user_ships_to_draw.pop()
                    num_ships_list[len(deleted_ship) - 1] -= 1
                    update_used_blocks(deleted_ship, used_blocks_for_manual_drawing.discard)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                drawing = True
                x_start, y_start = event.pos
                start = x_start, y_start
                ship_size = (0, 0)
            elif drawing and event.type == pygame.MOUSEMOTION:
                x_end, y_end = event.pos
                end = x_end, y_end
                ship_size = x_end - x_start, y_end - y_start
            elif drawing and event.type == pygame.MOUSEBUTTONUP:
                x_end, y_end = event.pos
                drawing = False
                ship_size = (0, 0)
                start_block = ((x_start - left_margin) // block_size + 1,
                               (y_start - upper_margin) // block_size + 1)
                end_block = ((x_end - left_margin) // block_size + 1,
                             (y_end - upper_margin) // block_size + 1)
                if start_block > end_block:
                    start_block, end_block = end_block, start_block
                temp_ship = []
                if 15 < start_block[0] < 26 and \
                        0 < start_block[1] < 11 and \
                        15 < end_block[0] < 26 and \
                        0 < end_block[1] < 11:
                    screen.fill(BLUE, message_rect_for_drawing_ships)
                    if start_block[0] == end_block[0] and \
                            (end_block[1] - start_block[1]) < 4:
                        for block in range(start_block[1], end_block[1] + 1):
                            temp_ship.append((start_block[0], block))
                    elif start_block[1] == end_block[1] and (end_block[0] - start_block[0]) < 4:
                        for block in range(start_block[0], end_block[0] + 1):
                            temp_ship.append((block, start_block[1]))
                    else:
                        screen.fill(BLUE, rect_for_fields)
                        computer_field = Field(0, comp)
                        user_field = Field(15, user)
                        del_button.draw_button()
                        del_button.print_message_for_button()
                        del_button.change_color_on_hover()
                        show_message_at_rect_center("Слишком большой корабль! Попробуй ещё раз!",
                                                    message_rect_for_drawing_ships)
                else:
                    screen.fill(BLUE, rect_for_fields)
                    computer_field = Field(0, comp)
                    user_field = Field(15, user)
                    del_button.draw_button()
                    del_button.print_message_for_button()
                    del_button.change_color_on_hover()
                    show_message_at_rect_center(
                        "Корабль вне вашего поля! Попробуй ещё раз!", message_rect_for_drawing_ships)
                if temp_ship:
                    temp_ship_set = set(temp_ship)
                    if ship_is_valid(temp_ship_set, used_blocks_for_manual_drawing):
                        if check_ships_numbers(temp_ship, num_ships_list):
                            num_ships_list[len(temp_ship) - 1] += 1
                            user_ships_to_draw.append(temp_ship)
                            user_ships_set |= temp_ship_set
                            update_used_blocks(
                                temp_ship, used_blocks_for_manual_drawing.add)
                        else:
                            screen.fill(BLUE, rect_for_fields)
                            computer_field = Field(0, comp)
                            user_field = Field(15, user)
                            del_button.draw_button()
                            del_button.print_message_for_button()
                            del_button.change_color_on_hover()
                            show_message_at_rect_center(f"Уже достаточно кораблей длины {len(temp_ship)}!",
                                                        message_rect_for_drawing_ships)
                    else:
                        screen.fill(BLUE, rect_for_fields)
                        computer_field = Field(0, comp)
                        user_field = Field(15, user)
                        del_button.draw_button()
                        del_button.print_message_for_button()
                        del_button.change_color_on_hover()
                        show_message_at_rect_center("Cоприкосновение кораблей! Не надо так",
                                                    message_rect_for_drawing_ships)
            if len(user_ships_to_draw) == 10:
                ships_not_created = False
                user_ships_working = copy.deepcopy(user_ships_to_draw)
                screen.fill(BLUE, rect_for_messages_and_buttons)
        if 20 * block_size - 20 < start[0] and start[0] + ship_size[0] < 30 * block_size + 20 \
                and \
                2 * block_size - 10 < start[1] and start[1] + ship_size[1] < 12 * block_size + 30:
            pygame.draw.rect(screen, BLACK, (start, ship_size), 3)
        draw_ships(user_ships_to_draw)
        pygame.display.update()

    while not game_over:
        draw_ships(destroyed_computer_ships)
        draw_ships(user_ships_to_draw)
        if not (dotted_set | hit_blocks):
            show_message_at_rect_center("   Начало игры! Твой ход!   ", message_rect_computer)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif not computer_turn and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if (left_margin < x < left_margin + 10 * block_size) and (
                        upper_margin < y < upper_margin + 10 * block_size):
                    sz = len(user_steps)
                    fired_block = ((x - left_margin) // block_size + 1, (y - upper_margin) // block_size + 1)
                    computer_turn = not hit_or_miss(fired_block, computer_ships_working, False, computer.ships,
                                                    computer.ships_set)
                    draw_from_dotted_set(dotted_set)
                    draw_hit_blocks(hit_blocks)
                    screen.fill(BLUE, message_rect_computer)
                    if sz == len(user_steps):
                        show_message_at_rect_center(
                            f"Клетка {LETTERS[fired_block[0] - 1] + str(fired_block[1])} уже отстрелена!",
                            message_rect_computer)
                    else:
                        show_message_at_rect_center(
                            f"Последний ход: {LETTERS[fired_block[0] - 1] + str(fired_block[1])}",
                            message_rect_computer, color=BLACK)
                else:
                    show_message_at_rect_center("Нужно нажать на клетку вражеского поля", message_rect_computer)
        if computer_turn:
            set_to_shoot_from = computer_available_to_fire_set
            if around_last_computer_hit_set:
                set_to_shoot_from = around_last_computer_hit_set
            fired_block = computer_shoots(set_to_shoot_from)
            computer_turn = hit_or_miss(fired_block, user_ships_working, True, user_ships_to_draw, user_ships_set)
            draw_from_dotted_set(dotted_set)
            draw_hit_blocks(hit_blocks)
            screen.fill(BLUE, message_rect_user)
            show_message_at_rect_center(
                f"Последний выстрел оппонента: {LETTERS[fired_block[0] - 16] + str(fired_block[1])}", message_rect_user,
                color=BLACK)
        if not computer.ships_set:
            show_message_at_rect_center("ПОБЕДА!", (0, 0, size[0], size[1]), game_over_font)
            game_over = True
        if not user_ships_set:
            show_message_at_rect_center("ПОРАЖЕНИЕ!", (0, 0, size[0], size[1]), game_over_font)
            game_over = True
        pygame.display.update()
    decided_to_play_again = False
    while game_over and not decided_to_play_again:
        screen.fill(BLUE, rect_for_messages_and_buttons)
        quit_button.draw_button()
        quit_button.change_color_on_hover()
        again_button.draw_button()
        again_button.change_color_on_hover()
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and quit_button.rect.collidepoint(mouse):
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and again_button.rect.collidepoint(mouse):
                decided_to_play_again = True
                break
        pygame.display.update()

    if decided_to_play_again:
        computer_available_to_fire_set = {(x, y)
                                          for x in range(16, 26) for y in range(1, 11)}
        around_last_computer_hit_set = set()
        dotted_set_for_computer_not_to_shoot = set()
        hit_blocks_for_computer_not_to_shoot = set()
        last_hits_list = []

        hit_blocks = set()
        dotted_set = set()
        user_steps = set()
        computer_steps = set()
        destroyed_computer_ships = []
        computer = Ships(0)
        computer_ships_working = copy.deepcopy(computer.ships)
        main()


main()
