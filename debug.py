from api_handler import APIHandler
import config

if __name__ == "__main__":
    handler = APIHandler()
    result = handler.get_access_token(config.USERNAME, "CVnm5200")
    print(result)
