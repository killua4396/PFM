from sshtunnel import SSHTunnelForwarder
import pymysql

DIALECT = 'mysql'
DRIVER = 'pymysql'

USERNAME = 'SWORD'
PASSWORD = 'SwordRefersToS11'
HOST = 'localhost'
PORT = 3306
DATABASE = 'sword'

ssh_host = '106.15.10.138'
ssh_user = 'root'
ssh_password = 'Redhome@)@)'
ssh_port = 22

forwarding_server = SSHTunnelForwarder(
    (ssh_host,ssh_port),
    ssh_username=ssh_user,
    ssh_password=ssh_password,
    remote_bind_address=(HOST,PORT)
)
forwarding_server.start()
local_port = forwarding_server.local_bind_port
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://SWORD:SwordRefersToS11@127.0.0.1:{}/sword'.format(local_port)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True
SECRET_KEY = "SwordRefersToS11"