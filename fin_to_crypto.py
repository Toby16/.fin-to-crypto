#!/usr/bin/env python3

import uvicorn, FIN_TO_CRYPTO


if __name__ == "__main__":
    config = uvicorn.Config("FIN_TO_CRYPTO:app", port=5000, log_level="info", reload=True)
    server = uvicorn.Server(config)
    server.run()
