class MobileConverter:
    # 匹配手机号
    regex = '1[3-9]\d{9}'

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return int(value)