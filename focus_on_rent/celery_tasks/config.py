# Celery的配置文件

# 指定消息队列：在ihome我们使用redis数据库做消息队列
# 我们选择redis的3号库作为消息队列
broker_url = 'redis://127.0.0.1:6379/3'
result_backend = 'redis://127.0.0.1:6379/4'

task_serializer = 'json'
result_serializer = 'json'
