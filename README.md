# AcTEC


## 安装

1. 点击此按钮添加 [HACS](https://hacs.xyz/) 自定义存储库

    [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=AcTECElectronics&repository=ha_actec_home&category=integration)

2. 完成之后点击此按钮添加集成

    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=actec)


## 调试

集成开启 debug 级日志的方法：

```yaml
# configuration.yaml 设置打印日志等级

logger:
  default: warning
  logs:
    custom_components.actec: debug
```
