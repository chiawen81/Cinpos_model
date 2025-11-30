"""
衰退預警服務
根據歷史統計資料判斷電影票房衰退預警等級
"""

from typing import Dict, List, Optional, Literal

try:
    from .decline_statistics import get_decline_statistics
except ImportError:
    from decline_statistics import get_decline_statistics

# 預警等級定義
WarningLevel = Literal["正常", "注意", "嚴重"]


class DeclineWarningService:
    """衰退預警服務類別"""

    def __init__(self):
        """初始化衰退預警服務"""
        self.statistics_service = get_decline_statistics()

    def check_decline_warning(
        self,
        opening_strength: float,
        current_week: int,
        predicted_decline_rate: float,
    ) -> Dict:
        """
        檢查衰退預警

        Args:
            opening_strength: 前兩周日均票房
            current_week: 當前週次
            predicted_decline_rate: 預測的衰退率（負值表示衰退）

        Returns:
            預警資訊字典，包含：
            - level: 預警等級（"正常", "注意", "嚴重"）
            - message: 預警訊息
            - predicted_decline_rate: 預測衰退率
            - average_decline_rate: 歷史平均衰退率
            - decline_speed_ratio: 衰退速度比率（相對於歷史平均）
            - tier: 電影量級
        """
        # 確保統計資料已載入
        self.statistics_service.calculate_statistics()

        # 1. 判斷電影量級
        tier = self.statistics_service.get_tier_for_strength(opening_strength)

        # 2. 取得該量級在當前週次的平均衰退率
        avg_decline_rate = self.statistics_service.get_average_decline_rate(tier, current_week)

        # 如果沒有歷史資料，無法判斷
        if avg_decline_rate is None:
            return {
                "level": "正常",
                "message": "當前週次缺少歷史資料，無法判斷預警",
                "predicted_decline_rate": predicted_decline_rate,
                "average_decline_rate": None,
                "decline_speed_ratio": None,
                "tier": tier,
            }

        # 3. 計算衰退速度比率
        # 如果歷史平均衰退率接近 0，無法計算比率
        if abs(avg_decline_rate) < 0.01:
            decline_speed_ratio = 0
        else:
            # 衰退速度比率 = (預測衰退率 - 平均衰退率) / abs(平均衰退率)
            # 例如：預測 -60%，平均 -40%，比率 = (-0.6 - (-0.4)) / 0.4 = -0.5 (衰退快 50%)
            decline_speed_ratio = (predicted_decline_rate - avg_decline_rate) / abs(
                avg_decline_rate
            )

        # 4. 判斷預警等級
        level, message = self._determine_warning_level(
            predicted_decline_rate, avg_decline_rate, decline_speed_ratio
        )

        return {
            "level": level,
            "message": message,
            "predicted_decline_rate": predicted_decline_rate,
            "average_decline_rate": avg_decline_rate,
            "decline_speed_ratio": decline_speed_ratio,
            "tier": tier,
        }

    def _determine_warning_level(
        self,
        predicted_decline_rate: float,
        avg_decline_rate: float,
        decline_speed_ratio: float,
    ) -> tuple[WarningLevel, str]:
        """
        判斷預警等級

        判斷邏輯：
        - 衰退比歷史平均快 30% 以下：正常
        - 衰退比歷史平均快 30%-50%：注意
        - 衰退比歷史平均快 50% 以上：嚴重

        Args:
            predicted_decline_rate: 預測衰退率
            avg_decline_rate: 平均衰退率
            decline_speed_ratio: 衰退速度比率

        Returns:
            (預警等級, 預警訊息)
        """
        # 注意：衰退率是負值，所以 decline_speed_ratio < 0 表示衰退更快

        if decline_speed_ratio >= -0.3:
            # 衰退速度正常或更慢
            return "正常", f"預測衰退率 {predicted_decline_rate:.1%}，符合歷史平均 {avg_decline_rate:.1%}"

        elif decline_speed_ratio >= -0.5:
            # 衰退比平均快 30%-50%
            faster_pct = abs(decline_speed_ratio) * 100
            return (
                "注意",
                f"預測衰退率 {predicted_decline_rate:.1%}，比歷史平均快 {faster_pct:.0f}%",
            )

        else:
            # 衰退比平均快 50% 以上
            faster_pct = abs(decline_speed_ratio) * 100
            return (
                "嚴重",
                f"預測衰退率 {predicted_decline_rate:.1%}，比歷史平均快 {faster_pct:.0f}%",
            )

    def batch_check_warnings(
        self, opening_strength: float, predictions: List[Dict]
    ) -> List[Dict]:
        """
        批次檢查多週預測的預警

        Args:
            opening_strength: 前兩周日均票房
            predictions: 預測結果列表，每個元素包含 {"week": int, "decline_rate": float, ...}

        Returns:
            包含預警資訊的預測結果列表
        """
        results = []

        for pred in predictions:
            week = pred["week"]
            decline_rate = pred.get("decline_rate", 0)

            # 檢查預警
            warning = self.check_decline_warning(opening_strength, week, decline_rate)

            # 將預警資訊加入預測結果
            pred_with_warning = pred.copy()
            pred_with_warning["warning"] = warning

            results.append(pred_with_warning)

        return results


# 單例模式
_instance = None


def get_decline_warning_service() -> DeclineWarningService:
    """
    取得衰退預警服務單例

    Returns:
        DeclineWarningService 實例
    """
    global _instance
    if _instance is None:
        _instance = DeclineWarningService()
    return _instance
