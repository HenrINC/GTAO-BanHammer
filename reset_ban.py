from gta_banhammer.middleware_lib import BanHammerMiddleware
from gta_banhammer.tables import BannedPlayer

middleware = BanHammerMiddleware()
session = middleware.Session()
try:
    # Delete all entries from the banned_players table
    session.query(BannedPlayer).delete()
    session.commit()
    print("All banned players have been reset.")
except Exception as e:
    print(f"An error occurred: {e}")
    session.rollback()
finally:
    session.close()
