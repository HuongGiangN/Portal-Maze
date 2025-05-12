import pygame
import pytmx
import os
import time
from collections import deque
from queue import PriorityQueue

# Cài đặt màn hình và các thông số
WIDTH, HEIGHT = 512, 512
TILE_SIZE = 32
ROWS, COLS = HEIGHT // TILE_SIZE, WIDTH // TILE_SIZE

# Màu sắc
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Khởi tạo màn hình
pygame.init()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("A* Pathfinding with Portal")
def show_start_screen():
    font = pygame.font.SysFont("Arial", 48)
    button_font = pygame.font.SysFont("Arial", 30)
    title_text = font.render("Portal", True, BLACK)
    start_text = button_font.render("Start", True, BLACK)
    
    # Load ảnh nền
    bg_image_path = os.path.join("Asset", "bg.jpg")
    if os.path.exists(bg_image_path):
        bg_image = pygame.image.load(bg_image_path).convert()
        bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))
        WIN.blit(bg_image, (0, 0))
    else:
        WIN.fill(BLACK)

    WIN.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3))

    # Vẽ nút Start
    start_rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2, 120, 50)
    pygame.draw.rect(WIN, WHITE, start_rect)
    pygame.draw.rect(WIN, BLACK, start_rect, 2)
    WIN.blit(start_text, (start_rect.centerx - start_text.get_width() // 2, start_rect.centery - start_text.get_height() // 2))

    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if start_rect.collidepoint(mx, my):
                    waiting = False

def select_mode():
    font = pygame.font.SysFont("Arial", 30)
    mode_text = font.render("Select Mode:", True, WHITE)
    bg_image = pygame.image.load(os.path.join("Asset", "bg.jpg")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    # Tạo các nút
    buttons = [("Auto", "auto"), ("Manual", "manual")]
    button_rects = []

    WIN.blit(bg_image, (0, 0))
    WIN.blit(mode_text, (WIDTH // 2 - mode_text.get_width() // 2, HEIGHT // 4))

    for i, (label_text, value) in enumerate(buttons):
        label = font.render(label_text, True, BLACK)
        rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 - 30 + i * 60, 120, 50)
        pygame.draw.rect(WIN, WHITE, rect)
        pygame.draw.rect(WIN, BLACK, rect, 2)
        WIN.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
        button_rects.append((rect, value))

    pygame.display.update()

    selected_mode = None
    while selected_mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for rect, value in button_rects:
                    if rect.collidepoint(mx, my):
                        selected_mode = value
    return selected_mode



def select_algorithm():
    font = pygame.font.SysFont("Arial", 30)
    title_text = font.render("Select Algorithm:", True, WHITE)
    bg_image = pygame.image.load(os.path.join("Asset", "bg.jpg")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    # Tên các thuật toán và danh sách button
    algorithms = [("A*", "astar"), ("IDA*", "idastar"), ("Greedy", "greedy"), ("BFS", "bfs")]
    buttons = []

    # Vị trí bắt đầu vẽ các nút
    start_y = HEIGHT // 2 - 80
    for i, (text, key) in enumerate(algorithms):
        label = font.render(text, True, BLACK)
        rect = pygame.Rect(WIDTH // 2 - 60, start_y + i * 60, 120, 50)
        buttons.append((rect, key, label))

    # Vẽ nền và tiêu đề
    WIN.blit(bg_image, (0, 0))
    WIN.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

    # Vẽ các nút
    for rect, _, label in buttons:
        pygame.draw.rect(WIN, WHITE, rect)
        pygame.draw.rect(WIN, BLACK, rect, 2)
        WIN.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

    pygame.display.update()

    selected = None
    while selected is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for rect, key, _ in buttons:
                    if rect.collidepoint(mx, my):
                        selected = key
    return selected


# Load bản đồ từ file TMX
def load_level_map(filename):
    tmx_data = pytmx.util_pygame.load_pygame(filename)
    layers = {
        "floor": [],
        "obstical": [],
        "portal": [],
        "end": [],
    }
    portal_positions = []

    for layer_name in layers:
        tmx_layer = tmx_data.get_layer_by_name(layer_name)
        if not isinstance(tmx_layer, pytmx.TiledTileLayer):
            print(f"Warning: Layer '{layer_name}' is not a TileLayer.")
            continue

        for y in range(tmx_data.height):
            row = []
            for x in range(tmx_data.width):
                tile = tmx_layer.data[y][x] if y < len(tmx_layer.data) and x < len(tmx_layer.data[y]) else 0
                row.append(tile)
                if layer_name == "portal" and tile != 0:
                    portal_positions.append((x, y))
            layers[layer_name].append(row)

    return layers, portal_positions, (tmx_data.width, tmx_data.height)

# Load tất cả tileset trong TMX
def load_tileset(tmx_data):
    tileset_images = {}
    for tileset in tmx_data.tilesets:
        for tile_id in range(tileset.tilecount):
            gid = tileset.firstgid + tile_id
            try:
                image = tmx_data.get_tile_image_by_gid(gid)
                if image:
                    tileset_images[gid] = image
            except IndexError:
                None
    return tileset_images

# Vẽ bản đồ
def draw_map(layers, tileset, surface):
    for y, row in enumerate(layers["floor"]):
        for x, tile in enumerate(row):
            if tile != 0:
                tile_img = tileset.get(tile)
                if tile_img:
                    tile_img = pygame.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                    surface.blit(tile_img, (x * TILE_SIZE, y * TILE_SIZE))

    for layer_name in ["obstical", "detail", "portal", "end"]:
        if layer_name in layers:
            for y, row in enumerate(layers[layer_name]):
                for x, tile in enumerate(row):
                    if tile != 0:
                        tile_img = tileset.get(tile)
                        if tile_img:
                            tile_img = pygame.transform.scale(tile_img, (TILE_SIZE, TILE_SIZE))
                            surface.blit(tile_img, (x * TILE_SIZE, y * TILE_SIZE))

# Cắt sprite nhân vật từ file PNG
def load_character_tiles(image_path, tile_width, tile_height):
    image = pygame.image.load(image_path).convert_alpha()
    tiles = {
        "down": [],
        "up": [],
        "left": [],
        "right": []
    }
    directions = ["down", "up", "left", "right"]

    for col, direction in enumerate(directions):
        for row in range(4):  # 4 frames mỗi hướng
            rect = pygame.Rect(col * tile_width, row * tile_height, tile_width, tile_height)
            tile = image.subsurface(rect)
            tiles[direction].append(tile)

    return tiles

def draw_timer(surface, elapsed_time):
    font = pygame.font.SysFont("Arial", 24)
    time_text = font.render(f"{elapsed_time:.1f}s", True, WHITE)

    # Hình chữ nhật nhỏ hơn, chỉ vừa đủ hiển thị số giây
    rect_width = 70
    rect_height = 40
    rect_x = WIDTH - rect_width - 10
    rect_y = 10

    pygame.draw.rect(surface, BLACK, (rect_x, rect_y, rect_width, rect_height))
    pygame.draw.rect(surface, WHITE, (rect_x, rect_y, rect_width, rect_height), 2)

    surface.blit(time_text, (rect_x + 10, rect_y + 8))



# Xác định hàng xóm
def get_neighbors(node, layers, portal_map):
    x, y = node
    neighbors = []

    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < COLS and 0 <= ny < ROWS:
            if layers["obstical"][ny][nx] == 0:
                neighbors.append((nx, ny))

    if node in portal_map:
        neighbors.append(portal_map[node])

    return neighbors

# Heuristic cho A*
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Thuật toán A*
def a_star(start, goal, layers, portal_map, greedy=False):
    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while not open_set.empty():
        _, current = open_set.get()

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        for neighbor in get_neighbors(current, layers, portal_map):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                if greedy:
                    f = heuristic(neighbor, goal)  # chỉ dùng heuristic
                else:
                    f = tentative_g + heuristic(neighbor, goal)                
                f_score[neighbor] = f
                open_set.put((f, neighbor))

    return []

# Thuật toán BFS
def bfs(start, goal, layers, portal_map):
    queue = deque([start])
    came_from = {start: None}
    visited = set([start])

    while queue:
        current = queue.popleft()
        if current == goal:
            break

        for neighbor in get_neighbors(current, layers, portal_map):
            if neighbor not in visited:
                visited.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

    if goal not in came_from:
        return []

    path = []
    current = goal
    while current in came_from and came_from[current] is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

# Thuật toán IDA*
def ida_star(start, goal, layers, portal_map):
    if start == goal:
        return [start]

    threshold = heuristic(start, goal)

    def search(path, g, threshold, visited):
        current = path[-1]
        f = g + heuristic(current, goal)

        if f > threshold:
            return f, None
        if current == goal:
            return f, list(path)

        min_threshold = float("inf")
        for neighbor in get_neighbors(current, layers, portal_map):
            if neighbor in visited:
                continue
            path.append(neighbor)
            visited.add(neighbor)

            t, result = search(path, g + 1, threshold, visited)

            if result is not None:
                return t, result
            if t < min_threshold:
                min_threshold = t

            path.pop()
            visited.remove(neighbor)

        return min_threshold, None

    path = [start]
    visited = set([start])

    while True:
        t, result = search(path, 0, threshold, visited)
        if result is not None:
            return result
        if t == float("inf"):
            return []
        threshold = t



# Lấy vị trí bắt đầu và đích
def find_positions(layers):
    start = (0, 0)
    end = None
    for y, row in enumerate(layers["end"]):
        for x, tile in enumerate(row):
            if tile != 0:
                end = (x, y)
    return start, end

# Hiển thị màn hình chọn độ khó
def display_menu():
    font = pygame.font.SysFont("Arial", 30)
    start_text = font.render("Select Difficulty:", True, BLACK )
    bg_image = pygame.image.load(os.path.join("Asset", "bg.jpg")).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    WIN.blit(bg_image, (0, 0))
    WIN.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 4 - start_text.get_height() // 2))

    difficulties = [("Easy", "easy"), ("Medium", "medium"), ("Hard", "hard")]
    button_rects = []

    for i, (label_text, value) in enumerate(difficulties):
        label = font.render(label_text, True, BLACK)
        rect = pygame.Rect(WIDTH // 2 - 60, HEIGHT // 2 - 60 + i * 60, 120, 50)
        pygame.draw.rect(WIN, WHITE, rect)
        pygame.draw.rect(WIN, BLACK, rect, 2)
        WIN.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))
        button_rects.append((rect, value))

    pygame.display.update()

    selected = None
    while selected is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for rect, value in button_rects:
                    if rect.collidepoint(mx, my):
                        selected = value
    return selected


def build_portal_map(layers, tmx_data):
    portal_layer = tmx_data.get_layer_by_name("portal")
    portal_map = {}
    portals_by_gid = {}

    for y in range(tmx_data.height):
        for x in range(tmx_data.width):
            tile = portal_layer.data[y][x]
            if tile != 0:
                if tile not in portals_by_gid:
                    portals_by_gid[tile] = []
                portals_by_gid[tile].append((x, y))

    # Tạo cặp từ các portal có cùng tile ID
    for positions in portals_by_gid.values():
        if len(positions) >= 2:
            for i in range(0, len(positions) - 1, 2):
                a, b = positions[i], positions[i + 1]
                portal_map[a] = b
                portal_map[b] = a

    return portal_map

def show_win_screen(elapsed_time=None):
    font = pygame.font.SysFont("Arial", 48)
    small_font = pygame.font.SysFont("Arial", 30)
    win_text = font.render("You Win!", True, (255, 0, 0))
    quit_text = small_font.render("Back to Menu", True, (0, 0, 0))
    bg_image = os.path.join("Asset", "bg.jpg")
    bg_image = pygame.image.load(bg_image).convert()
    bg_image = pygame.transform.scale(bg_image, (WIDTH, HEIGHT))

    WIN.blit(bg_image, (0, 0))
    WIN.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 3))

    if elapsed_time is not None:
        time_text = small_font.render(f"Time: {elapsed_time:.1f}s", True, WHITE)
        WIN.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, HEIGHT // 2))

    quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    WIN.blit(quit_text, quit_rect)
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if quit_rect.collidepoint(mx, my):
                    return True  # Chỉ khi click Quit mới quay lại




# Main game loop
def main():
    while True:
        clock = pygame.time.Clock()
        direction = "down"
        anim_frame = 0
        anim_counter = 0
        running = True

        # Load âm thanh
        portal_sound = pygame.mixer.Sound(os.path.join("sounds", "portal.wav"))
        goal_sound = pygame.mixer.Sound(os.path.join("sounds", "goal.wav"))

        show_start_screen()
        difficulty = display_menu()
        mode = select_mode()

        # Map file logic
        map_file = os.path.join(os.getcwd(), f"{difficulty}.tmx")

        # Load map
        tmx_data = pytmx.util_pygame.load_pygame(map_file)
        layers, portal_positions, (map_width, map_height) = load_level_map(map_file)
        tileset = load_tileset(tmx_data)
        character_image_path = os.path.join("Asset", "Ninja Adventure - Asset Pack", "Actor", "Characters", "NinjaDark", "SeparateAnim", "Walk.png")
        character_tiles = load_character_tiles(character_image_path, 16, 16)
        portal_map = build_portal_map(layers, tmx_data)
        start, end = find_positions(layers)
        player_pos = start

        if mode == "auto":
            algorithm = select_algorithm()
            if algorithm == "astar":
                start_algo_time = time.time()
                path = a_star(start, end, layers, portal_map)
                end_algo_time = time.time()
                print(f"A*: {end_algo_time - start_algo_time:.6f} seconds.")
            elif algorithm == "greedy":
                start_algo_time = time.time()
                path = a_star(start, end, layers, portal_map, greedy=True)
                end_algo_time = time.time()
                print(f"Greedy: {end_algo_time - start_algo_time:.6f} seconds.")
            elif algorithm == "bfs":
                start_algo_time = time.time()
                path = bfs(start, end, layers, portal_map)
                end_algo_time = time.time()
                print(f"BFS: {end_algo_time - start_algo_time:.6f} seconds.")
            elif algorithm == "idastar":
                start_algo_time = time.time()
                path = ida_star(start, end, layers, portal_map)
                end_algo_time = time.time()
                print(f"IDA*: {end_algo_time - start_algo_time:.6f} seconds.")

            if not path:
                print("Không tìm thấy đường đi!")
            else:
                print(f"Đường đi: {path}")

            path_index = 0
            start_time = pygame.time.get_ticks()
            while running:
                clock.tick(5)
                WIN.fill(BLACK)
                draw_map(layers, tileset, WIN)
                elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
                draw_timer(WIN, elapsed_time)

                character_tile = character_tiles[direction][anim_frame]
                character_tile = pygame.transform.scale(character_tile, (TILE_SIZE, TILE_SIZE))
                WIN.blit(character_tile, (player_pos[0] * TILE_SIZE, player_pos[1] * TILE_SIZE))
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()

                if path_index < len(path):
                    current = path[path_index]
                    dx = current[0] - player_pos[0]
                    dy = current[1] - player_pos[1]
                    direction = "right" if dx == 1 else "left" if dx == -1 else "down" if dy == 1 else "up"

                    if player_pos in portal_map and portal_map[player_pos] == current:
                        portal_sound.play()
                    player_pos = current

                    if player_pos == end:
                        goal_sound.play()
                        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
                        should_restart = show_win_screen(elapsed_time)
                        if should_restart:
                            break 
                        running = False

                    anim_counter += 1
                    if anim_counter >= 5:
                        anim_frame = (anim_frame + 1) % 4
                        anim_counter = 0
                    path_index += 1

        else:
            last_teleport_from = None
            start_time = pygame.time.get_ticks()
            while running:
                clock.tick(10)
                WIN.fill(BLACK)
                draw_map(layers, tileset, WIN)
                elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
                draw_timer(WIN, elapsed_time)

                dx, dy = 0, 0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            dy = -1
                            direction = "up"
                        elif event.key == pygame.K_DOWN:
                            dy = 1
                            direction = "down"
                        elif event.key == pygame.K_LEFT:
                            dx = -1
                            direction = "left"
                        elif event.key == pygame.K_RIGHT:
                            dx = 1
                            direction = "right"

                new_x, new_y = player_pos[0] + dx, player_pos[1] + dy
                if 0 <= new_x < COLS and 0 <= new_y < ROWS and layers["obstical"][new_y][new_x] == 0:
                    player_pos = (new_x, new_y)
                    if player_pos in portal_map and player_pos != last_teleport_from:
                        target = portal_map[player_pos]
                        last_teleport_from = target
                        player_pos = target
                        portal_sound.play()
                    else:
                        last_teleport_from = None

                    if player_pos == end:
                        goal_sound.play()
                        elapsed_time = (pygame.time.get_ticks() - start_time) / 1000
                        should_restart = show_win_screen(elapsed_time)
                        if should_restart:
                            break 
                        running = False

                character_tile = character_tiles[direction][anim_frame]
                character_tile = pygame.transform.scale(character_tile, (TILE_SIZE, TILE_SIZE))
                WIN.blit(character_tile, (player_pos[0] * TILE_SIZE, player_pos[1] * TILE_SIZE))

                pygame.display.update()

                anim_counter += 1
                if anim_counter >= 5:
                    anim_frame = (anim_frame + 1) % 4
                    anim_counter = 0


if __name__ == "__main__":
    main()
