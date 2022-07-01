import sys
from time import sleep

import pygame

from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from button import Button
from  scoreboard import Scoreboard


class AlienInvasion:
    """管理游戏资源和行为的类"""
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")

        # 创建一个用于存储游戏统计信息的实例
        self.stats = GameStats(self)

        # 创建记分牌
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # 创建Play按钮
        self.play_button = Button(self, "Play")


    def run_game(self):
        """开始游戏主循环"""
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_alien()

            self._update_screen()

    def _check_events(self):
        """响应键盘和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """在点击play按钮后开始游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # 重置游戏设置
            self.settings.initialize_dynamic_settings()

            # 重置统计信息
            self.stats.reset_stats()
            self.stats.game_active = True

            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            self.bullets.empty()
            self.aliens.empty()

            self._create_fleet()
            self.ship.center_ship()


            # 隐藏鼠标
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_q:
            sys.exit()

    def _check_keyup_events(self, event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _ship_hit(self):
        """响应飞船和外星人的碰撞"""
        if self.stats.ships_left > 0:
            # 飞船hp - 1
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # 清空外星人和子弹
            self.bullets.empty()
            self.aliens.empty()

            # 创建新的外星人群并将飞船放在屏幕中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入编组bullets中"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """更新子弹1位置并消除多余子弹"""
        # 更新子弹位置
        self.bullets.update()

        # 删除多余子弹
        for bullet in self.bullets.sprites():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """响应子弹和外星人的碰撞"""
        # 检查子弹是否击中敌人，是就删除相应子弹和外星人
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
        # 射杀全部外星人后删除所有子弹并创建新的外星人
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()
            self.stats.level += 1
            self.sb.prep_level()

    def _update_alien(self):
        """更新所有外星人位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检查外星人与飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """所有外星人到达边缘时采取相应措施"""
        for alien in self.aliens:
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _check_aliens_bottom(self):
        """检查外星人是否到达屏幕底部"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # 像飞船碰撞一样处理
                self._ship_hit()
                break

    def _change_fleet_direction(self):
        """"将外星人整体下移并改变方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _create_fleet(self):
        """创建外星人群"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        availabie_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = availabie_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height -
                             (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # 创建外星人群
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """创建一个外星人并放在当前行"""
        alien = Alien(self)
        alien_width = alien.rect.width
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number

        self.aliens.add(alien)

    def _update_screen(self):
        """更新屏幕"""
        # 如果游戏处于非活跃状态， 就绘制Play按钮
        if not self.stats.game_active:
            self.play_button.draw_button()
        else:
            self.screen.fill(self.settings.bg_color)
            self.ship.blitme()
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.aliens.draw(self.screen)
            self.sb.show_score()

        pygame.display.flip()


if __name__ == '__main__':
    # 创建实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()
