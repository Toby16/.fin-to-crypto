#!/usr/bin/env python3

import uvicorn


if __name__ == "__main__":
    config = uvicorn.Config("FIN_TO_CRYPTO:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    server.run()
