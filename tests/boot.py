import os,sys,asyncio
os.environ.setdefault("MONGO_URL","mongodb://x"); os.environ.setdefault("DB_NAME","okmain"); os.environ.setdefault("JWT_SECRET","t"*40)
os.environ["STORAGE_MODE"]="local"; os.environ.setdefault("UPLOAD_DIR","/tmp/ok_up")
import motor.motor_asyncio as m, mongomock_motor
m.AsyncIOMotorClient=lambda *a,**k: mongomock_motor.AsyncMongoMockClient()
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","panel"))
import server
