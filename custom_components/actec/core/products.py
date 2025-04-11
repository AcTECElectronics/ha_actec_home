PRODUCTS_INFO: dict[str, list[dict]] = {
    "16": [  # 1路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
    ],
    "17": [  # 2路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
    ],
    "18": [  # 3路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
        {"endpoint": 4, "platform": "switch", "type": "switch"},
    ],
    "20": [  # 1路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
    ],
    "21": [  # 2路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
    ],
    "22": [  # 3路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
        {"endpoint": 4, "platform": "light", "type": "brightness"},
    ],
    "27": [  # 4键情景面板
    ],
    "29": [  # 6键情景面板
    ],
    "32": [  # 4路开关情景面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
    ],
    "33": [  # 6路开关情景面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
        {"endpoint": 4, "platform": "switch", "type": "switch"},
    ],
    "34": [  # 4路调光情景面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
    ],
    "35": [  # 6路调光情景面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
        {"endpoint": 4, "platform": "light", "type": "brightness"},
    ],
    "36": [  # 色温面板
    ],
    "37": [  # rgb面板
    ],
    "38": [  # rgbtw面板
    ],
    "48": [  # 1路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
    ],
    "49": [  # 2路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
    ],
    "50": [  # 3路开关面板
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
        {"endpoint": 4, "platform": "switch", "type": "switch"},
    ],
    "52": [  # 1路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
    ],
    "53": [  # 2路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
    ],
    "54": [  # 3路调光面板
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
        {"endpoint": 4, "platform": "light", "type": "brightness"},
    ],
    "59": [  # 4键情景面板
    ],
    "61": [  # 6键情景面板
    ],
    "71": [  # 3路开关3路情景
        {"endpoint": 2, "platform": "switch", "type": "switch"},
        {"endpoint": 3, "platform": "switch", "type": "switch"},
        {"endpoint": 4, "platform": "switch", "type": "switch"},
    ],
    "72": [  # 3路调光3路情景
        {"endpoint": 2, "platform": "light", "type": "brightness"},
        {"endpoint": 3, "platform": "light", "type": "brightness"},
        {"endpoint": 4, "platform": "light", "type": "brightness"},
    ],
    "257": [  # 遥控器
    ],
    "259": [  # 手持遥控器
    ],
    "512": [  # 可控硅控制器
        {"endpoint": 2, "platform": "light", "type": "brightness"},
    ],
    "768": [
        # 代码内特殊处理
    ],
    "4097": [  # rgbtw驱动器
        {"endpoint": 1, "platform": "light", "type": "hs_color_temp"},
    ],
    "4098": [  # pwm控制器
        {"endpoint": 1, "platform": "light", "type": "hs_color_temp"},
    ],
    "4100": [  # 色温驱动器
        {"endpoint": 1, "platform": "light", "type": "color_temp"},
    ],
    "4101": [  # 色温驱动器
        {"endpoint": 1, "platform": "light", "type": "color_temp"},
    ],
    "4102": [  # 色温驱动器
        {"endpoint": 1, "platform": "light", "type": "color_temp"},
    ],
    "4103": [  # pwm控制器
        {"endpoint": 1, "platform": "light", "type": "hs_color_temp"},
    ],
    "4104": [  # 色温驱动器
        {"endpoint": 1, "platform": "light", "type": "color_temp"},
    ],
    "4105": [  # pwm控制器
        {"endpoint": 1, "platform": "light", "type": "hs_color_temp"},
    ],
    "4352": [  # 智能插座
        {"endpoint": 1, "platform": "switch", "type": "outlet"},
        {"endpoint": 1, "platform": "sensor", "type": "power"},
        {"endpoint": 1, "platform": "sensor", "type": "energy"},
    ],
    "4608": [  # 开合帘电机
        {"endpoint": 1, "platform": "cover", "type": "curtain"},
    ],
    "4609": [  # 卷帘电机
        {"endpoint": 1, "platform": "cover", "type": "roller"},
    ],
    "4865": [  # 感应器
        {"endpoint": 1, "platform": "sensor", "type": "illuminance"},
        {"endpoint": 1, "platform": "binary_sensor", "type": "motion"},
    ],
    "5120": [
        # 代码内特殊处理
    ],
    "5121": [
        # 代码内特殊处理
    ],
}
