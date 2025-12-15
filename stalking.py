import asyncio

from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

from tradingbot import place_order



# ======================================================
# CONFIG
# ======================================================

RPC_URL = "https://mainnet.base.org"

WATCHED_WALLETS = {
    "0xef7c11b7b19a0bae61c3dbb4de7dd043aaf1d7de",
    "0xa99515d2360963b65823ad4d983b5053d310dfac",
    "0xb9aea70c096fb84d19b8c4cc83de9743a921c945",
    "0x0e066ed845a6853557a0d580b3ba998b0283aca8"
    "0xceef7ce2af5e1a85afd6e4c48b9f01fc328d1af8",
    "0xf939518f99cb067ef371a00cdbabc9061f30e14b",
}

WATCHED_WALLETS = {w.lower() for w in WATCHED_WALLETS}

POLL_INTERVAL = 0.5  # seconds

APPROVE_SELECTOR = "095ea7b3"

# ======================================================
# CONNECT
# ======================================================

w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))

# ======================================================
# HELPERS
# ======================================================

def normalize_input(tx_input):
    return tx_input.hex() if isinstance(tx_input, bytes) else tx_input

def classify_tx(tx):
    tx_input = normalize_input(tx["input"])

    if tx_input.startswith(APPROVE_SELECTOR):
        return "APPROVE"

    if tx["to"] and tx_input != "0x":
        return "EXECUTE"

    return "TRANSFER"

def decode_approve(tx):
    """
    Decode ERC20 approve(address,uint256)
    """
    tx_input = normalize_input(tx["input"])[8:]
    spender = "0x" + tx_input[:64][24:]
    amount = int(tx_input[64:128], 16)
    return spender, amount

TOKEN_CACHE = {}

async def get_token_info(token_address):
    if token_address in TOKEN_CACHE:
        return TOKEN_CACHE[token_address]

    try:
        erc20 = w3.eth.contract(
            address=token_address,
            abi=[
                {
                    "name": "symbol",
                    "inputs": [],
                    "outputs": [{"type": "string"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "name": "decimals",
                    "inputs": [],
                    "outputs": [{"type": "uint8"}],
                    "stateMutability": "view",
                    "type": "function"
                },
            ]
        )
        symbol = await erc20.functions.symbol().call()
    except:
        symbol = "UNKNOWN"

    return symbol

# ======================================================
# MAIN MONITOR
# ======================================================

async def monitor():
    flag = [False]
    print("Connected to Base")
    print("Watching wallets:")
    for w in WATCHED_WALLETS:
        print(" -", w)

    last_block = await w3.eth.block_number
    print("Starting from block:", last_block)

    while True:
        try:
            latest_block = await w3.eth.block_number

            if latest_block > last_block:
                for block_number in range(last_block + 1, latest_block + 1):
                    block = await w3.eth.get_block(block_number, full_transactions=True)

                    for tx in block.transactions:
                        frm = tx["from"].lower()
                        to = tx["to"].lower() if tx["to"] else None

                        if frm in WATCHED_WALLETS or to in WATCHED_WALLETS:
                            wallet = frm if frm in WATCHED_WALLETS else to
                            tx_type = classify_tx(tx)

                            print("\n==============================")
                            print("WALLET:", wallet)
                            print("BLOCK:", block_number)
                            print("HASH :", tx["hash"].hex())
                            print("TYPE :", tx_type)

                            if tx_type == "APPROVE" and not flag[0]:
                                #spender, amount = decode_approve(tx)
                                token = tx["to"]
                                symbol = await get_token_info(token)
                                if symbol != "CHECK":
                                    print("placing buy order")
                                    place_order("buy")
                                    print("Symbol not check")
                                    flag[0] = True

                            elif tx_type == "EXECUTE":
                                if (flag[0]):
                                    place_order("sell")
                                    flag[0]=False
                                print("EXECUTED CONTRACT:", to)

                            else:
                                print("TRANSFER:", w3.from_wei(tx["value"], "ether"), "ETH")

                last_block = latest_block

            await asyncio.sleep(POLL_INTERVAL)

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(1)

# ======================================================
# RUN
# ======================================================

asyncio.run(monitor())






