class GameStats:
    """跟踪游戏的统计信息"""

    def __init__(self,ai_game):
        self.settings = ai_game.settings
        self.reset_stats()
        self.game_active = False

        # 最高得分，任何时候都不应该重置
        self.high_score = 0


    def reset_stats(self):
        """初始化游戏在运行期间可能变化的统计信息"""
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1
