from rq.decorators import job
from redis import Redis
import time
redis_conn = Redis()

job = add.delay(3, 4)
time.sleep(1)
print(job.result)