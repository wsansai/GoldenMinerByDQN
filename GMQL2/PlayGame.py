import pygame
import random
import math

# 初始化 pygame
pygame.init()

# 设置窗口尺寸
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Golden Miner")

# 加载背景图片，保留透明度
background_image = pygame.image.load('images/background2.jpg').convert_alpha()
# 缩放图片以适应窗口大小
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# 加载各类物体图片，保留透明度
small_golden_image = pygame.image.load('images/small_golden2.png').convert_alpha()
small_golden_image = pygame.transform.scale(small_golden_image, (150, 150))

large_golden_image = pygame.image.load('images/large_golden2.png').convert_alpha()
large_golden_image = pygame.transform.scale(large_golden_image, (200, 200))

diamond_image = pygame.image.load('images/diamond3.png').convert_alpha()
diamond_image = pygame.transform.scale(diamond_image, (100, 100))

bomb_image = pygame.image.load('images/bomb2.png').convert_alpha()
bomb_image = pygame.transform.scale(bomb_image, (120, 120))

stone_image = pygame.image.load('images/stone2.png').convert_alpha()

# 存储图片的字典，键为物体类型，值为对应的图片
object_images = {
    "small_gold": small_golden_image,
    "large_gold": large_golden_image,
    "diamond": diamond_image,
    "bomb": bomb_image,
    "stone": stone_image
}

# 加载爆炸图片，保留透明度
explosion_image = pygame.image.load('images/baozha.jpg').convert_alpha()
explosion_image = pygame.transform.scale(explosion_image, (60, 60))

# 加载勾爪头部图片，保留透明度
hook_head_image = pygame.image.load('images/hook2.png').convert_alpha()
hook_head_image = pygame.transform.scale(hook_head_image, (100, 100))  # 根据需要调整大小

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
ORANGE = (255, 165, 0)

# 字体
font = pygame.font.SysFont("Arial", 36)

# 游戏变量
clock = pygame.time.Clock()
score = 0
time_left = 30  # 游戏时间
game_over = False
game_stopped = False  # 游戏是否停止

# 钩子变量
hook_length = 0
hook_speed = 5 * 2  # 钩爪速度
original_hook_speed = hook_speed  # 记录钩子的原始速度
hook_angle = 90  # 初始角度为 90°（垂直向下）
hook_angle_speed = 2  # 钩子旋转速度（调快一些）
hook_state = "idle"  # idle, extending, retracting
hook_pos = [WIDTH // 2, 50]  # 钩子的起点（在窗口顶部中间）
hook_end_pos = [0, 0]  # 钩子的末端位置
fixed_angle = 90  # 钩子伸出时的固定角度
angle_direction = 1  # 角度变化方向：1 为增大，-1 为减小

# 被抓取的物体
grabbed_object = None  # 记录当前被抓取的物体

# 爆炸提示
explosion_pos = None  # 爆炸位置
explosion_timer = 0  # 爆炸提示的显示时间


# 物体类
class Object:
    def __init__(self, x, y, size, value, color, obj_type):
        self.x = x
        self.y = y
        self.size = size
        self.value = value
        self.color = color
        self.obj_type = obj_type  # 物体类型：small_gold, large_gold, diamond, stone, bomb

    def draw(self):
        if self.obj_type == "stone":
            # 根据石头大小动态缩放图片
            scaled_stone_image = pygame.transform.scale(stone_image, (self.size * 2, self.size * 2))
            screen.blit(scaled_stone_image,
                        (self.x - scaled_stone_image.get_width() // 2, self.y - scaled_stone_image.get_height() // 2))
        else:
            image = object_images[self.obj_type]
            screen.blit(image, (self.x - image.get_width() // 2, self.y - image.get_height() // 2))


# 检测两个物体是否重叠
def is_overlapping(obj1, obj2):
    distance = math.sqrt((obj1.x - obj2.x) ** 2 + (obj1.y - obj2.y) ** 2)
    return distance < (obj1.size + obj2.size)


# 创建初始物体（固定数量和类型）
def create_initial_objects():
    objects = []
    # 生成小金块（3个）
    for _ in range(3):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 25, 20, YELLOW, "small_gold")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # 生成大金块（2个）
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 40, 35, YELLOW, "large_gold")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # 生成钻石（2个）
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, 15, 50, BLUE, "diamond")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # 生成炸弹（2个）
    for _ in range(2):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, random.randint(20, 40), 0, RED, "bomb")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    # 生成石头（3个）
    for _ in range(3):
        while True:
            x = random.randint(100, WIDTH - 100)
            y = random.randint(hook_pos[1] + 100, HEIGHT - 100)
            new_obj = Object(x, y, random.randint(60, 100), 1, GRAY, "stone")
            if not any(is_overlapping(new_obj, obj) for obj in objects):
                objects.append(new_obj)
                break

    return objects


# 计算钩子的最大长度（不超过窗口边界）
def calculate_max_length(angle):
    # 钩子的起点
    x0, y0 = hook_pos

    # 计算钩子末端与窗口边界的交点
    # 根据角度计算钩子的方向
    dx = math.cos(math.radians(angle))
    dy = math.sin(math.radians(angle))

    # 计算与窗口上下左右边界的交点
    if dx > 0:
        x_boundary = WIDTH
    else:
        x_boundary = 0
    if dy > 0:
        y_boundary = HEIGHT
    else:
        y_boundary = 0

    # 计算与 x 边界的交点
    t_x = (x_boundary - x0) / dx if dx != 0 else float('inf')
    # 计算与 y 边界的交点
    t_y = (y_boundary - y0) / dy if dy != 0 else float('inf')

    # 取最小的 t 值（即最近的交点）
    t = min(t_x, t_y)

    # 最大长度为交点距离
    return t


# 初始化物体
objects = create_initial_objects()

# 游戏主循环
running = True
while running:
    screen.blit(background_image, (0, 0))

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 键盘事件处理
        if event.type == pygame.KEYDOWN and not game_stopped:
            if event.key == pygame.K_SPACE and hook_state == "idle":
                hook_state = "extending"
                fixed_angle = hook_angle  # 记录发射时的固定角度

    # 自动旋转钩子角度
    if hook_state == "idle" and not game_stopped:
        hook_angle += hook_angle_speed * angle_direction

        # 角度到达 180° 或 0° 时反转方向
        if hook_angle >= 180:
            angle_direction = -1  # 反转方向，从 180° 返回到 0°
        elif hook_angle <= 0:
            angle_direction = 1  # 反转方向，从 0° 返回到 180°

    # 更新钩子状态
    if hook_state == "extending":
        max_length = calculate_max_length(fixed_angle)  # 计算当前角度的最大长度
        hook_length += hook_speed
        if hook_length > max_length:
            hook_state = "retracting"
    elif hook_state == "retracting":
        hook_length -= hook_speed
        if hook_length <= 0:
            hook_length = 0
            hook_state = "idle"

            # 钩子回到原点后，移除被抓取的物体并增加得分
            if grabbed_object:
                if grabbed_object.obj_type == "stone":
                    score += 1  # 石头得分增加1
                elif grabbed_object.obj_type != "bomb":  # 炸弹不增加得分
                    score += grabbed_object.value  # 其他物体增加原始分值

                objects.remove(grabbed_object)
                new_obj = create_initial_objects()[0]  # 生成一个新物体
                objects.append(new_obj)
                grabbed_object = None

            # 恢复钩子的原始速度
            hook_speed = original_hook_speed

    # 计算钩子末端位置
    if hook_state == "extending" or hook_state == "retracting":
        # 使用固定角度
        hook_end_pos[0] = hook_pos[0] + hook_length * math.cos(math.radians(fixed_angle))
        hook_end_pos[1] = hook_pos[1] + hook_length * math.sin(math.radians(fixed_angle))
    else:
        # 使用当前角度
        hook_end_pos[0] = hook_pos[0] + hook_length * math.cos(math.radians(hook_angle))
        hook_end_pos[1] = hook_pos[1] + hook_length * math.sin(math.radians(hook_angle))

    # 绘制预览虚线（仅在钩子未伸出时显示）
    if hook_state == "idle" and not game_stopped:
        max_length = calculate_max_length(hook_angle)  # 计算当前角度的最大长度
        preview_end_pos = (
            hook_pos[0] + max_length * math.cos(math.radians(hook_angle)),
            hook_pos[1] + max_length * math.sin(math.radians(hook_angle))
        )
        pygame.draw.line(screen, GRAY, hook_pos, preview_end_pos, 2)

    # 绘制钩子
    pygame.draw.line(screen, WHITE, hook_pos, hook_end_pos, 5)
    # 旋转钩子图片
    rotated_hook_image = pygame.transform.rotate(hook_head_image,
                                                 90 - hook_angle if hook_state == "idle" else 90 - fixed_angle)
    hook_rect = rotated_hook_image.get_rect(center=(int(hook_end_pos[0]), int(hook_end_pos[1])))

    # 绘制旋转后的钩子图片
    screen.blit(rotated_hook_image, hook_rect)

    # 绘制物体
    for obj in objects:
        obj.draw()

        # 检测钩子是否抓取物体
        if hook_state == "extending" and grabbed_object is None and not game_stopped:
            distance = math.sqrt((obj.x - hook_end_pos[0]) ** 2 + (obj.y - hook_end_pos[1]) ** 2)
            if distance < obj.size + 10:
                grabbed_object = obj  # 记录被抓取的物体
                if obj.obj_type == "stone":
                    hook_speed = original_hook_speed / 3  # 抓取石头后钩子速度减慢
                elif obj.obj_type == "large_gold":
                    hook_speed = original_hook_speed / 2  # 抓取大金块后钩子速度减慢
                elif obj.obj_type == "bomb":
                    explosion_pos = (obj.x, obj.y)  # 记录爆炸位置
                    explosion_timer = 30  # 爆炸提示显示30帧
                    time_left -= 10  # 倒计时减少10秒
                    hook_state = "idle"  # 钩子立即收回
                    hook_length = 0
                    grabbed_object = None  # 炸弹不跟随钩子移动
                    objects.remove(obj)  # 移除炸弹
                    new_obj = create_initial_objects()[0]  # 生成一个新物体
                    objects.append(new_obj)
                hook_state = "retracting"

    if grabbed_object and grabbed_object.obj_type != "bomb":
        grabbed_object.x = hook_end_pos[0]
        grabbed_object.y = hook_end_pos[1]
        grabbed_object.draw()  # 再次绘制被抓取的物体

    # 旋转钩子图片
    rotated_hook_image = pygame.transform.rotate(hook_head_image,
                                                 90 - hook_angle if hook_state == "idle" else 90 - fixed_angle)
    hook_rect = rotated_hook_image.get_rect(center=(int(hook_end_pos[0]), int(hook_end_pos[1])))
    screen.blit(rotated_hook_image, hook_rect)


    # 显示爆炸提示
    if explosion_timer > 0:
        screen.blit(explosion_image, (explosion_pos[0] - explosion_image.get_width() // 2,
                                      explosion_pos[1] - explosion_image.get_height() // 2))
        explosion_timer -= 1

    # 显示得分和时间
    score_text = font.render(f"Score: {score}", True, (0,0,0))
    time_text = font.render(f"Time: {int(time_left)}", True, (0,0,0))
    screen.blit(score_text, (10, 10))
    screen.blit(time_text, (WIDTH - 150, 10))

    # 更新时间
    if not game_over and not game_stopped:
        time_left -= 1 / 60  # 每帧减少时间
        if time_left <= 0:
            game_over = True

    # 游戏结束
    if game_over or game_stopped:
        # 显示游戏结束文字
        game_over_text = font.render("Game Over! Final Score: " + str(score), True, RED)
        screen.blit(game_over_text, (WIDTH // 2 - 200, HEIGHT // 2 - 50))
        # 重置游戏变量
        score = 0
        time_left = 30
        game_over = False
        game_stopped = False
        hook_length = 0
        hook_state = "idle"
        hook_angle = 90  # 重置勾爪角度为初始角度90°
        grabbed_object = None
        objects = create_initial_objects()  # 重新生成初始物体

    pygame.display.flip()
    clock.tick(60)

pygame.quit()